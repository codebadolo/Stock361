from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Stock, MouvementStock, Inventaire, LigneInventaire
from .forms import MouvementStockForm, InventaireForm, LigneInventaireForm
from produit.models import Produit
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from entreprise.models import Entreprise ,Utilisateur
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from .models import Inventaire, LigneInventaire
from produit.models import Produit
from django.contrib.auth.decorators import login_required
# ----------------- STOCK -----------------
class StockListView(LoginRequiredMixin, ListView):
    model = Stock
    template_name = 'stock/stock_list.html'
    context_object_name = 'stocks'

    def get_queryset(self):
        return Stock.objects.filter(entreprise=self.request.user.entreprise)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stocks = context['stocks']

        total_produits = stocks.count()
        total_quantite = sum(s.quantite for s in stocks)

        stock_critique = stocks.filter(quantite__lte=5).count()  # seuil modifiable

        context.update({
            'total_produits': total_produits,
            'total_quantite': total_quantite,
            'stock_critique': stock_critique,
        })
        return context


# ----------------- MOUVEMENTS -----------------
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from .models import Stock, MouvementStock, Inventaire, LigneInventaire
from produit.models import Produit
from entreprise.models import Utilisateur
import json
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Count
from .models import MouvementStock
from produit.models import Produit
from entreprise.models import Utilisateur

class MouvementStockListView(LoginRequiredMixin, ListView):
    model = MouvementStock
    template_name = 'stock/mouvement_list.html'
    context_object_name = 'mouvements'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = MouvementStock.objects.filter(
            entreprise=self.request.user.entreprise
        ).select_related('produit', 'utilisateur').order_by('-date')
        
        # Filtres simples
        type_filter = self.request.GET.get('type')
        if type_filter in ['entree', 'sortie', 'ajustement']:
            queryset = queryset.filter(type_mouvement=type_filter)
        
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        if date_debut:
            queryset = queryset.filter(date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__lte=date_fin)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Produits pour le modal
        context['produits'] = Produit.objects.filter(
            entreprise=entreprise
        ).select_related('stock').order_by('nom')
        
        # Statistiques simples
        mouvements = self.get_queryset()
        context['stats'] = {
            'total': mouvements.count(),
            'entrees': mouvements.filter(type_mouvement='entree').count(),
            'sorties': mouvements.filter(type_mouvement='sortie').count(),
            'ajustements': mouvements.filter(type_mouvement='ajustement').count(),
        }
        
        return context

@login_required
def ajouter_mouvement(request):
    if request.method == 'POST':
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            produit = form.cleaned_data['produit']
            type_mouvement = form.cleaned_data['type_mouvement']
            quantite = form.cleaned_data['quantite']

            stock, _ = Stock.objects.get_or_create(
                entreprise=request.user.entreprise,
                produit=produit,
                defaults={'quantite': 0}
            )
            avant = stock.quantite

            if type_mouvement == 'entree':
                stock.quantite += quantite
            elif type_mouvement == 'sortie':
                stock.quantite -= quantite
            elif type_mouvement == 'ajustement':
                stock.quantite = quantite

            stock.save()

            mouvement = form.save(commit=False)
            mouvement.entreprise = request.user.entreprise
            mouvement.utilisateur = request.user
            mouvement.avant = avant
            mouvement.apres = stock.quantite
            mouvement.save()

            messages.success(request, "Mouvement enregistré !")
            return redirect('stock_list')
    else:
        form = MouvementStockForm()
    return render(request, 'stock/mouvement_form.html', {'form': form})

# ----------------- INVENTAIRE -----------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Inventaire, LigneInventaire, Stock
from produit.models import Produit

@login_required
def creer_inventaire(request):
    if request.method == 'POST':
        form = InventaireForm(request.POST)
        if form.is_valid():
            inventaire = form.save(commit=False)
            inventaire.entreprise = request.user.entreprise
            inventaire.utilisateur = request.user
            inventaire.save()

            # Filtrer seulement les produits avec du stock (> 0)
            produits_avec_stock = Produit.objects.filter(
                entreprise=request.user.entreprise,
                stock__quantite__gt=0  # Seulement ceux avec stock > 0
            ).select_related('stock').distinct()
            
            # OU si vous voulez inclure aussi les produits sans stock mais avec une fiche
            # produits = Produit.objects.filter(
            #     entreprise=request.user.entreprise
            # ).select_related('stock')
            
            for produit in produits_avec_stock:
                LigneInventaire.objects.create(
                    inventaire=inventaire,
                    produit=produit,
                    quantite_theorique=produit.stock.quantite if produit.stock else 0,
                    quantite_comptee=0
                )
            
            messages.success(request, f"Inventaire créé avec {produits_avec_stock.count()} produits en stock.")
            return redirect('detail_inventaire', inventaire.id)
    else:
        form = InventaireForm()
    
    # Pour afficher les statistiques dans le formulaire
    produits_avec_stock = Produit.objects.filter(
        entreprise=request.user.entreprise,
        stock__quantite__gt=0
    ).select_related('stock')
    
    produits_sans_stock = Produit.objects.filter(
        entreprise=request.user.entreprise
    ).filter(
        Q(stock__isnull=True) | Q(stock__quantite=0)
    )
    
    context = {
        'form': form,
        'produits_count': produits_avec_stock.count(),
        'stock_total': sum(p.stock.quantite for p in produits_avec_stock if p.stock),
        'stock_critique': produits_avec_stock.filter(stock__quantite__lte=5).count(),
        'stock_zero': produits_sans_stock.count(),
    }
    
    return render(request, 'stock/inventaire_form.html', context)


class InventaireListView(LoginRequiredMixin, ListView):
    model = Inventaire
    template_name = 'stock/inventaire_list.html'
    context_object_name = 'inventaires'
    paginate_by = 20
    
    def get_queryset(self):
        return Inventaire.objects.filter(
            entreprise=self.request.user.entreprise
        ).select_related('utilisateur').prefetch_related('lignes').order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Statistiques
        inventaires = self.get_queryset()
        context['stats'] = {
            'total': inventaires.count(),
            'completed': inventaires.filter(lignes__isnull=False).distinct().count(),
            'in_progress': inventaires.filter(lignes__isnull=True).count(),
            'discrepancies': LigneInventaire.objects.filter(
                inventaire__entreprise=entreprise,
                ecart__gt=0
            ).count(),
        }
        
        # Utilisateurs pour les filtres
        context['utilisateurs'] = entreprise.utilisateurs.all().order_by('username')
        
        # Template filters
        from django.template.defaulttags import register
        
        @register.filter
        def completed_count(lignes):
            return lignes.filter(quantite_comptee__gt=0).count()
        
        @register.filter
        def ecarts_count(lignes):
            return lignes.filter(ecart__gt=0).count()
        
        return context
@login_required
def detail_inventaire(request, pk):
    inventaire = get_object_or_404(
        Inventaire, 
        pk=pk, 
        entreprise=request.user.entreprise
    )
    
    # Récupérer seulement les lignes pour les produits avec stock initial
    lignes = inventaire.lignes.filter(
        quantite_theorique__gt=0
    ).select_related('produit', 'produit__stock').all()
    
    if request.method == 'POST':
        # Sauvegarder les quantités comptées
        for ligne in lignes:
            field_name = f'quantite_{ligne.id}'
            if field_name in request.POST:
                quantite = request.POST.get(field_name, '').strip()
                if quantite:
                    try:
                        ligne.quantite_comptee = int(quantite)
                        ligne.save()
                    except ValueError:
                        messages.error(request, f"Valeur invalide pour {ligne.produit.nom}")
        
        messages.success(request, "Les quantités ont été enregistrées !")
        
        # Vérifier si on doit appliquer les ajustements
        if request.POST.get('apply_adjustments'):
            appliquer_ajustements(inventaire)
            messages.info(request, "Les ajustements de stock ont été appliqués.")
        
        return redirect('inventaire_detail', pk=pk)
    
    # Calculer les statistiques
    lignes_completed = lignes.filter(quantite_comptee__isnull=False).count()
    
    context = {
        'inventaire': inventaire,
        'lignes': lignes,
        'lignes_completed': lignes_completed,
    }
    
    return render(request, 'stock/inventaire_detail.html', context)


def appliquer_ajustements(inventaire):
    """Applique les ajustements de stock suite à un inventaire"""
    from .models import MouvementStock, Stock
    
    lignes_avec_ecart = inventaire.lignes.filter(ecart__isnull=False).exclude(ecart=0)
    
    for ligne in lignes_avec_ecart:
        # Mettre à jour le stock
        stock, created = Stock.objects.get_or_create(
            entreprise=inventaire.entreprise,
            produit=ligne.produit,
            defaults={'quantite': ligne.quantite_comptee}
        )
        
        avant = stock.quantite
        stock.quantite = ligne.quantite_comptee
        stock.save()
        
        # Créer un mouvement d'ajustement
        MouvementStock.objects.create(
            entreprise=inventaire.entreprise,
            produit=ligne.produit,
            type_mouvement='ajustement',
            quantite=ligne.ecart,
            avant=avant,
            apres=stock.quantite,
            utilisateur=inventaire.utilisateur,
            commentaire=f"Ajustement inventaire #{inventaire.id}"
        )
    
    # Marquer l'inventaire comme terminé
    inventaire.save()
@login_required
def get_stock_data(request):
    """Retourne les données de stock en JSON pour le formulaire"""
    stocks = Stock.objects.filter(entreprise=request.user.entreprise)
    data = {str(stock.produit_id): stock.quantite for stock in stocks}
    return JsonResponse(data)


# dans views.py
from django.http import JsonResponse
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Stock, MouvementStock
from produit.models import Produit

@login_required
@csrf_exempt
def ajouter_mouvement_ajax(request):
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            produit_id = request.POST.get('produit')
            type_mouvement = request.POST.get('type_mouvement')
            quantite = request.POST.get('quantite')
            commentaire = request.POST.get('commentaire', '')
            
            # Validation des données requises
            if not all([produit_id, type_mouvement, quantite]):
                return JsonResponse({
                    'success': False,
                    'error': 'Tous les champs obligatoires doivent être remplis'
                }, status=400)
            
            try:
                quantite = int(quantite)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'La quantité doit être un nombre valide'
                }, status=400)
            
            if quantite <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'La quantité doit être supérieure à 0'
                }, status=400)
            
            # Vérifier que le type de mouvement est valide
            if type_mouvement not in ['entree', 'sortie', 'ajustement']:
                return JsonResponse({
                    'success': False,
                    'error': 'Type de mouvement invalide'
                }, status=400)
            
            # Récupérer le produit
            produit = get_object_or_404(
                Produit, 
                id=produit_id,
                entreprise=request.user.entreprise
            )
            
            # Récupérer ou créer le stock
            stock, created = Stock.objects.get_or_create(
                entreprise=request.user.entreprise,
                produit=produit,
                defaults={'quantite': 0}
            )
            
            avant = stock.quantite
            
            # Appliquer le mouvement
            if type_mouvement == 'entree':
                stock.quantite += quantite
            elif type_mouvement == 'sortie':
                stock.quantite -= quantite
            elif type_mouvement == 'ajustement':
                stock.quantite = quantite
            
            stock.save()
            
            # Créer le mouvement dans l'historique
            mouvement = MouvementStock.objects.create(
                entreprise=request.user.entreprise,
                produit=produit,
                type_mouvement=type_mouvement,
                quantite=quantite,
                avant=avant,
                apres=stock.quantite,
                utilisateur=request.user,
                commentaire=commentaire
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Mouvement enregistré avec succès',
                'mouvement_id': mouvement.id
            })
            
        except Produit.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Produit non trouvé'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur serveur: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    }, status=405)

    