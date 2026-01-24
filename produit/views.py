from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Produit, Categorie
from .forms import ProduitForm, CategorieForm
from entreprise.models import Entreprise
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum, F, Value
from django.db.models.functions import Concat
import json
import pandas as pd
from io import BytesIO
import datetime

# ===================== PRODUITS =====================
class ProduitListView(LoginRequiredMixin, ListView):
    model = Produit
    template_name = 'produit/produit_list.html'
    context_object_name = 'produits'
    #paginate_by = 
    
    def get_queryset(self):
        user = self.request.user
        search_query = self.request.GET.get('search', '').strip()
        categorie_id = self.request.GET.get('categorie', '')
        etat_stock = self.request.GET.get('etat_stock', '')
        
        # Base queryset optimisé
        queryset = Produit.objects.select_related('categorie').only(
            'id', 'reference', 'nom', 'description', 'image',
            'prix_achat', 'prix_vente_detail', 'prix_vente_gros',
            'stock_minimum', 'est_actif', 'date_creation',
            'categorie__id', 'categorie__nom'
        )
        
        # Filtrage par entreprise
        if user.est_super_admin or user.est_responsable:
            queryset = queryset.all()
        else:
            queryset = queryset.filter(entreprise=user.entreprise)
        
        # Filtrage par recherche
        if search_query:
            queryset = queryset.filter(
                Q(nom__icontains=search_query) |
                Q(reference__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(categorie__nom__icontains=search_query)
            )
        
        # Filtrage par catégorie
        if categorie_id and categorie_id != 'all':
            queryset = queryset.filter(categorie_id=categorie_id)
        
        # Filtrage par état de stock
        if etat_stock and etat_stock != 'all':
            # Pour l'état de stock, on doit annoter d'abord
            queryset = queryset.annotate(
                current_stock=Coalesce(F('stock__quantite'), Value(0))
            )
            if etat_stock == 'rupture':
                queryset = queryset.filter(current_stock=0)
            elif etat_stock == 'critique':
                queryset = queryset.filter(
                    current_stock__gt=0,
                    current_stock__lt=F('stock_minimum')
                )
            elif etat_stock == 'normal':
                queryset = queryset.filter(current_stock__gte=F('stock_minimum'))
        
        # Tri par défaut
        queryset = queryset.order_by('-date_creation')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistiques
        qs = self.get_queryset()
        context['total_produits'] = qs.count()
        
        # Calcul des états de stock
        context['total_rupture'] = sum(1 for p in qs if p.etat_stock == 'rupture')
        context['total_critique'] = sum(1 for p in qs if p.etat_stock == 'critique')
        context['total_normal'] = sum(1 for p in qs if p.etat_stock == 'normal')
        
        # Catégories pour le filtre
        context['categories'] = Categorie.objects.filter(entreprise=user.entreprise)
        
        # Paramètres de filtrage
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_categorie'] = self.request.GET.get('categorie', 'all')
        context['selected_etat'] = self.request.GET.get('etat_stock', 'all')
        
        return context

# Vue pour les détails d'un produit (JSON pour modales)
@login_required
def produit_detail_json(request, pk):
    """Retourne les détails d'un produit en JSON"""
    try:
        produit = get_object_or_404(Produit.objects.select_related('categorie'), 
                                   pk=pk, entreprise=request.user.entreprise)
        
        data = {
            'id': produit.id,
            'nom': produit.nom,
            'reference': produit.reference,
            'categorie': produit.categorie.id if produit.categorie else '',
            'description': produit.description or '',
            'prix_achat': str(produit.prix_achat) if produit.prix_achat else '',
            'prix_vente_detail': str(produit.prix_vente_detail),
            'prix_vente_gros': str(produit.prix_vente_gros) if produit.prix_vente_gros else '',
            'stock_minimum': produit.stock_minimum,
            'est_actif': produit.est_actif,
            'image_url': produit.image.url if produit.image else '',
            'image_name': produit.image.name if produit.image else '',
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# Création via modal AJAX
@csrf_exempt
@login_required
def produit_create_ajax(request):
    """Créer un produit via AJAX"""
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                produit = form.save(commit=False)
                produit.entreprise = request.user.entreprise
                produit.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Produit créé avec succès !',
                    'produit': {
                        'id': produit.id,
                        'nom': produit.nom,
                        'reference': produit.reference,
                        'categorie': produit.categorie.nom if produit.categorie else '',
                        'prix_vente_detail': str(produit.prix_vente_detail),
                        'etat_stock': produit.etat_stock,
                        'image_url': produit.image.url if produit.image else ''
                    }
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [str(e)]}
                })
        else:
            # Formatage des erreurs pour le frontend
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                'success': False,
                'errors': errors
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    })

# Modification via modal AJAX
@csrf_exempt
@login_required
def produit_update_ajax(request, pk):
    """Modifier un produit via AJAX"""
    produit = get_object_or_404(Produit, pk=pk, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        
        if form.is_valid():
            try:
                form.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Produit modifié avec succès !',
                    'produit': {
                        'id': produit.id,
                        'nom': produit.nom,
                        'reference': produit.reference,
                        'categorie': produit.categorie.nom if produit.categorie else '',
                        'prix_vente_detail': str(produit.prix_vente_detail),
                        'etat_stock': produit.etat_stock,
                        'image_url': produit.image.url if produit.image else ''
                    }
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [str(e)]}
                })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                'success': False,
                'errors': errors
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    })

@csrf_exempt
@login_required
def categorie_update_ajax(request, pk):
    """Modifier une catégorie via AJAX"""
    categorie = get_object_or_404(Categorie, pk=pk, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        form = CategorieForm(request.POST, instance=categorie, entreprise=request.user.entreprise)
        
        if form.is_valid():
            try:
                form.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Catégorie modifiée avec succès !',
                    'categorie': {
                        'id': categorie.id,
                        'nom': categorie.nom,
                        'full_name': str(categorie)
                    }
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [str(e)]}
                })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                'success': False,
                'errors': errors
            })
# Suppression via AJAX
@csrf_exempt
@login_required
@require_http_methods(["POST"])
def produit_delete_ajax(request, pk):
    """Supprimer un produit via AJAX"""
    produit = get_object_or_404(Produit, pk=pk, entreprise=request.user.entreprise)
    
    try:
        produit_nom = produit.nom
        produit.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Produit "{produit_nom}" supprimé avec succès !'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# Export Excel
@login_required
def export_produits_excel(request):
    """Exporter les produits en Excel"""
    user = request.user
    
    # Récupérer les produits
    if user.est_super_admin or user.est_responsable:
        produits = Produit.objects.select_related('categorie').all()
    else:
        produits = Produit.objects.select_related('categorie').filter(entreprise=user.entreprise)
    
    # Préparer les données
    data = []
    for produit in produits:
        data.append({
            'Référence': produit.reference,
            'Nom': produit.nom,
            'Catégorie': produit.categorie.nom if produit.categorie else '',
            'Description': produit.description or '',
            'Prix Achat': float(produit.prix_achat) if produit.prix_achat else 0,
            'Prix Vente Détail': float(produit.prix_vente_detail),
            'Prix Vente Gros': float(produit.prix_vente_gros) if produit.prix_vente_gros else 0,
            'Stock Minimum': produit.stock_minimum,
            'Stock Actuel': produit.quantite_stock if hasattr(produit, 'quantite_stock') else 0,
            'État Stock': produit.etat_stock,
            'Statut': 'Actif' if produit.est_actif else 'Inactif',
            'Date Création': produit.date_creation.strftime('%d/%m/%Y %H:%M')
        })
    
    # Créer le DataFrame
    df = pd.DataFrame(data)
    
    # Créer la réponse Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Produits', index=False)
        
        # Ajuster la largeur des colonnes
        worksheet = writer.sheets['Produits']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    # Préparer la réponse
    filename = f'produits_export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# Vue détail produit
class ProduitDetailView(LoginRequiredMixin, DetailView):
    model = Produit
    template_name = 'produit/produit_detail.html'
    context_object_name = 'produit'
    
    def get_queryset(self):
        user = self.request.user
        if user.est_super_admin or user.est_responsable:
            return Produit.objects.select_related('categorie', 'entreprise')
        return Produit.objects.select_related('categorie').filter(entreprise=user.entreprise)

# ===================== CATEGORIES =====================
class CategorieListView(LoginRequiredMixin, ListView):
    model = Categorie
    template_name = 'produit/categorie_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Categorie.objects.filter(entreprise=self.request.user.entreprise)
        
@csrf_exempt
@login_required
def categorie_create_ajax(request):
    """Créer une catégorie via AJAX"""
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        
        if form.is_valid():
         
            categorie = form.save(commit=False)
            categorie.entreprise = request.user.entreprise
            categorie.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Catégorie créée avec succès !',
                'categorie': {
                    'id': categorie.id,
                    'nom': categorie.nom,
                    'full_name': str(categorie)
                }
            })

        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                'success': False,
                'errors': errors
            })

# Fonction utilitaire pour Coalesce (si nécessaire)
from django.db.models import Func, Value

class Coalesce(Func):
    function = 'COALESCE'
    template = '%(function)s(%(expressions)s)'
@csrf_exempt    
@login_required
def produit_create_modal(request):
    """Créer un produit via modal AJAX"""
    # Implementation would be similar to produit_create_ajax
    pass