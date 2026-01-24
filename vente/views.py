# vente/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.files.base import ContentFile
from datetime import timedelta
import json
import os
from io import BytesIO

# ReportLab pour génération PDF
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from PIL import Image as PILImage

from .models import Vente, LigneVente, Client
from produit.models import Produit
from stock.models import Stock, MouvementStock
from .forms import ClientForm
from .utils import generate_receipt_pdf, generate_invoice_pdf
# ============================================
# UTILITAIRES POUR LES RECUS PDF
# ============================================

# Dans vente/views.py - Modifier la fonction generate_receipt
@login_required
def generate_receipt(request, pk, doc_type='receipt'):
    """
    Génère un document PDF (reçu ou facture) pour une vente existante.
    doc_type: 'receipt' pour reçu, 'invoice' pour facture
    """
    vente = get_object_or_404(Vente, pk=pk)
    
    if not request.user.est_super_admin and vente.entreprise != request.user.entreprise:
        messages.error(request, "Accès non autorisé.")
        return redirect('vente_list')
    
    try:
        if doc_type == 'invoice':
            pdf_content = generate_invoice_pdf(vente)
            filename = f"facture_{vente.id}_{vente.date.strftime('%Y%m%d')}.pdf"
        else:
            pdf_content = generate_receipt_pdf(vente)
            filename = f"recu_{vente.id}_{vente.date.strftime('%Y%m%d')}.pdf"
        
        # Sauvegarder
        vente.recu_pdf.save(filename, ContentFile(pdf_content))
        vente.save()
        
        messages.success(request, f"{'Facture' if doc_type == 'invoice' else 'Reçu'} généré avec succès!")
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération: {str(e)}")
    
    return redirect('vente_detail', pk=vente.pk)

# Ajouter une vue pour choisir le type de document
@login_required
def generate_document(request, pk):
    """
    Page pour choisir le type de document à générer
    """
    vente = get_object_or_404(Vente, pk=pk)
    
    if request.method == "POST":
        doc_type = request.POST.get('doc_type', 'receipt')
        return generate_receipt(request, pk, doc_type)
    
    return render(request, 'vente/generate_document.html', {'vente': vente})

# Modifier la fonction view_receipt pour accepter un paramètre type
@login_required
def view_receipt(request, pk, doc_type=None):
    """
    Affiche le reçu ou la facture dans le navigateur.
    Si doc_type est 'invoice', génère une facture à la volée
    """
    vente = get_object_or_404(Vente, pk=pk)
    
    if not request.user.est_super_admin and vente.entreprise != request.user.entreprise:
        return HttpResponse("Accès non autorisé", status=403)
    
    try:
        if doc_type == 'invoice':
            # Générer une facture à la volée
            pdf_content = generate_invoice_pdf(vente)
            filename = f"facture_{vente.id}.pdf"
        elif vente.recu_pdf:
            # Utiliser le reçu existant
            response = HttpResponse(vente.recu_pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="recu_vente_{vente.id}.pdf"'
            return response
        else:
            messages.warning(request, "Aucun document disponible.")
            return redirect('vente_detail', pk=vente.pk)
        
        # Pour les documents générés à la volée
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('vente_detail', pk=vente.pk)

def save_receipt_to_vente(vente):
    """
    Génère et sauvegarde le reçu PDF pour une vente.
    """
    try:
        pdf_content = generate_receipt_pdf(vente)
        
        # Nom du fichier
        filename = f"recu_{vente.id}_{vente.date.strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Sauvegarder
        vente.recu_pdf.save(filename, ContentFile(pdf_content))
        vente.save()
        
        return True
    except Exception as e:
        print(f"Erreur sauvegarde reçu: {e}")
        return False

# ============================================
# VUES PRINCIPALES
# ============================================

# vente/views.py
class VenteListView(LoginRequiredMixin, ListView):
    model = Vente
    template_name = "vente/vente_list.html"
    context_object_name = "page_obj"  # Pour la pagination
    paginate_by = 20  # Nombre d'éléments par page
    
    def get_queryset(self):
        user = self.request.user
        queryset = Vente.objects.all()
        
        if not user.est_super_admin:
            queryset = queryset.filter(entreprise=user.entreprise)
        
        # Filtres
        period = self.request.GET.get('period', 'today')
        if period == 'today':
            today = timezone.now().date()
            queryset = queryset.filter(date__date=today)
        elif period == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(date__gte=week_ago)
        elif period == 'month':
            month_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(date__gte=month_ago)
        
        client_id = self.request.GET.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(id__icontains=search) |
                Q(client__nom__icontains=search) |
                Q(lignes__produit__nom__icontains=search)
            ).distinct()
        
        # Tri
        sort = self.request.GET.get('sort')
        if sort:
            try:
                sort_int = int(sort)
                if sort_int > 0:
                    field = self.get_sort_field(abs(sort_int))
                    if field:
                        queryset = queryset.order_by(field)
                else:
                    field = self.get_sort_field(abs(sort_int))
                    if field:
                        queryset = queryset.order_by(f'-{field}')
            except ValueError:
                pass
        
        # Tri par défaut (date décroissante)
        if not sort:
            queryset = queryset.order_by('-date')
        
        return queryset
    
    def get_sort_field(self, column_index):
        """Retourne le champ de tri correspondant à l'index de colonne"""
        sort_map = {
            0: 'id',        # ID
            1: 'date',      # Date
            2: 'client__nom',  # Client
            4: 'total',     # Montant
            5: 'id',        # Statut (par défaut tri par ID)
        }
        return sort_map.get(column_index)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        
        # Statistiques pour AUJOURD'HUI uniquement
        ventes_aujourdhui = Vente.objects.filter(
            entreprise=user.entreprise,
            date__date=today
        ) if not user.est_super_admin else Vente.objects.filter(date__date=today)
        
        # Nombre de ventes aujourd'hui
        context['ventes_aujourdhui'] = ventes_aujourdhui.count()
        
        # Chiffre d'affaires aujourd'hui
        ca_aujourdhui = ventes_aujourdhui.aggregate(total=Sum('total'))['total'] or 0
        context['ca_aujourdhui'] = ca_aujourdhui
        
        # Produits vendus aujourd'hui
        produits_vendus_aujourdhui = LigneVente.objects.filter(
            vente__in=ventes_aujourdhui
        ).aggregate(total=Sum('quantite'))['total'] or 0
        context['produits_vendus_aujourdhui'] = produits_vendus_aujourdhui
        
        # Clients servis aujourd'hui (distincts)
        clients_aujourdhui = ventes_aujourdhui.filter(
            client__isnull=False
        ).values('client').distinct().count()
        context['clients_aujourdhui'] = clients_aujourdhui
        
        # Liste des clients pour le filtre
        context['clients_list'] = Client.objects.filter(
            entreprise=user.entreprise
        ) if not user.est_super_admin else Client.objects.all()
        
        # Paramètres actuels pour pré-remplir les filtres
        context['current_period'] = self.request.GET.get('period', 'today')
        context['current_client'] = self.request.GET.get('client', '')
        context['current_search'] = self.request.GET.get('search', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        
        return context

@login_required
def vente_detail(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    
    # Vérifier les permissions
    if not request.user.est_super_admin and vente.entreprise != request.user.entreprise:
        messages.error(request, "Accès non autorisé.")
        return redirect('vente_list')
    
    lignes = vente.lignes.all()
    
    context = {
        'vente': vente,
        'lignes': lignes,
    }
    
    return render(request, "vente/vente_detail.html", context)

@login_required
def api_stock_list(request):
    pass
    


# vente/views.py
@login_required
def vente_create(request):
    # Récupérer les produits en stock de l'entreprise
    produits = Produit.objects.select_related("categorie").prefetch_related("stock").filter(
        entreprise=request.user.entreprise,
        stock__quantite__gt=0
    ).distinct()
    
    # Récupérer les clients de l'entreprise
    clients = Client.objects.filter(entreprise=request.user.entreprise)
    
    if request.method == "POST":
        print("=" * 50)
        print("DEBUG - Formulaire POST reçu")
        print("POST data:", dict(request.POST))
        print("=" * 50)
        
        try:
            data = request.POST
            client_id = data.get("client", "").strip()
            
            print(f"DEBUG - Client ID brut: '{client_id}'")
            print(f"DEBUG - Type client_id: {type(client_id)}")
            print(f"DEBUG - client_id est vide? {client_id == ''}")
            print(f"DEBUG - client_id est None? {client_id is None}")
            
            cart_data_json = data.get("cart_data", "[]")
            cart_data = json.loads(cart_data_json)
            
            if not cart_data:
                messages.error(request, "Le panier est vide.")
                return render(request, "vente/vente_form.html", {
                    "produits": produits,
                    "clients": clients
                })
            
            with transaction.atomic():
                # DÉTERMINER LE CLIENT
                client = None
                if client_id and client_id != "" and client_id != "null":
                    try:
                        client = Client.objects.get(id=client_id, entreprise=request.user.entreprise)
                        print(f"DEBUG - Client trouvé: {client.nom} (ID: {client.id})")
                    except Client.DoesNotExist:
                        print(f"DEBUG - Client avec ID {client_id} non trouvé")
                        messages.error(request, "Client non trouvé.")
                        return render(request, "vente/vente_form.html", {
                            "produits": produits,
                            "clients": clients
                        })
                else:
                    print("DEBUG - Aucun client sélectionné (client comptant)")
                
                # Créer la vente
                vente = Vente.objects.create(
                    entreprise=request.user.entreprise,
                    client=client,  # Peut être None pour client comptant
                    utilisateur=request.user,
                    date=timezone.now(),
                    total=0
                )
                
                print(f"DEBUG - Vente créée: #{vente.id}")
                print(f"DEBUG - Client associé à la vente: {vente.client}")
                
                total_vente = 0
                
                for item in cart_data:
                    produit_id = item.get("produit_id")
                    quantite = int(item.get("quantite"))
                    prix_unitaire = float(item.get("prix_unitaire"))
                    
                    produit = Produit.objects.get(id=produit_id)
                    
                    stock = Stock.objects.get(
                        produit=produit,
                        entreprise=request.user.entreprise
                    )
                    
                    if stock.quantite < quantite:
                        raise Exception(f"Stock insuffisant pour {produit.nom}")
                    
                    total_ligne = quantite * prix_unitaire
                    
                    LigneVente.objects.create(
                        vente=vente,
                        produit=produit,
                        quantite=quantite,
                        prix_unitaire=prix_unitaire,
                        total=total_ligne
                    )
                    
                    stock.quantite -= quantite
                    stock.save()
                    
                    MouvementStock.objects.create(
                        entreprise=request.user.entreprise,
                        produit=produit,
                        type_mouvement='sortie',
                        quantite=quantite,
                        avant=stock.quantite + quantite,
                        apres=stock.quantite,
                        utilisateur=request.user,
                        commentaire=f"Vente #{vente.id}"
                    )
                    
                    total_vente += total_ligne
                
                vente.total = total_vente
                vente.save()
                
                # Générer le reçu PDF
                save_receipt_to_vente(vente)
                
                messages.success(request, f"Vente #{vente.id} enregistrée avec succès !")
                print(f"DEBUG - Redirection vers détail vente #{vente.id}")
                return redirect("vente_detail", pk=vente.pk)
                
        except json.JSONDecodeError:
            messages.error(request, "Erreur dans les données du panier.")
        except Client.DoesNotExist:
            messages.error(request, "Client non trouvé.")
        except Produit.DoesNotExist:
            messages.error(request, "Produit non trouvé.")
        except Stock.DoesNotExist:
            messages.error(request, "Stock non trouvé pour ce produit.")
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")
            import traceback
            traceback.print_exc()  # Pour voir l'erreur complète dans la console
        
        # En cas d'erreur, retourner au formulaire
        return render(request, "vente/vente_form.html", {
            "produits": produits,
            "clients": clients
        })
    
    # GET request - afficher le formulaire
    return render(request, "vente/vente_form.html", {
        "produits": produits,
        "clients": clients
    })

@login_required
def vente_delete(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    
    if not request.user.est_super_admin and vente.entreprise != request.user.entreprise:
        messages.error(request, "Accès non autorisé.")
        return redirect('vente_list')
    
    if request.method == "POST":
        vente.delete()
        messages.success(request, "Vente supprimée.")
        return redirect("vente_list")
    
    return render(request, "vente/vente_confirm_delete.html", {"vente": vente})

# ============================================
# VUES POUR LES RECUS PDF
# ============================================

@login_required
def generate_receipt(request, pk):
    """
    Génère un nouveau reçu PDF pour une vente existante.
    """
    vente = get_object_or_404(Vente, pk=pk)
    
    if not request.user.est_super_admin and vente.entreprise != request.user.entreprise:
        messages.error(request, "Accès non autorisé.")
        return redirect('vente_list')
    
    try:
        if save_receipt_to_vente(vente):
            messages.success(request, "Reçu généré avec succès!")
        else:
            messages.error(request, "Erreur lors de la génération du reçu.")
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
    
    return redirect('vente_detail', pk=vente.pk)

@login_required
def download_receipt(request, pk):
    """
    Télécharge le reçu PDF d'une vente.
    """
    vente = get_object_or_404(Vente, pk=pk)
    
    if not request.user.est_super_admin and vente.entreprise != request.user.entreprise:
        return HttpResponse("Accès non autorisé", status=403)
    
    if not vente.recu_pdf:
        messages.warning(request, "Aucun reçu disponible.")
        return redirect('vente_detail', pk=vente.pk)
    
    try:
        response = HttpResponse(vente.recu_pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recu_vente_{vente.id}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('vente_detail', pk=vente.pk)

@login_required
def view_receipt(request, pk):
    """
    Affiche le reçu PDF dans le navigateur.
    """
    vente = get_object_or_404(Vente, pk=pk)
    
    if not request.user.est_super_admin and vente.entreprise != request.user.entreprise:
        return HttpResponse("Accès non autorisé", status=403)
    
    if not vente.recu_pdf:
        messages.warning(request, "Aucun reçu disponible.")
        return redirect('vente_detail', pk=vente.pk)
    
    try:
        response = HttpResponse(vente.recu_pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="recu_vente_{vente.id}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('vente_detail', pk=vente.pk)

# ============================================
# VUES POUR LES CLIENTS
# ============================================

class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'vente/client_list.html'
    context_object_name = 'clients'
    
    def get_queryset(self):
        user = self.request.user
        if user.est_super_admin:
            return Client.objects.all()
        return Client.objects.filter(entreprise=user.entreprise)

@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.entreprise = request.user.entreprise
            client.save()
            messages.success(request, "Client ajouté avec succès")
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'vente/client_form.html', {'form': form})

# vente/views.py
import json
from django.http import JsonResponse

@login_required
def client_create_ajax(request):
    """
    Création de client via AJAX pour le POS.
    """
    if request.method == "POST":
        try:
            # Accepter les données JSON ou FormData
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                nom = data.get("nom", "").strip()
                contact = data.get("contact", "").strip()
            else:
                nom = request.POST.get("nom", "").strip()
                contact = request.POST.get("contact", "").strip()
            
            print(f"DEBUG - Nom reçu: '{nom}'")
            print(f"DEBUG - Contact reçu: '{contact}'")
            
            if not nom:
                return JsonResponse({
                    "success": False,
                    "error": "Le nom du client est requis"
                })
            
            # Créer le client
            client = Client.objects.create(
                entreprise=request.user.entreprise,
                nom=nom,
                contact=contact if contact else None
            )
            
            print(f"DEBUG - Client créé: ID={client.id}, Nom={client.nom}")
            
            return JsonResponse({
                "success": True,
                "id": client.id,
                "nom": client.nom
            })
            
        except Exception as e:
            print(f"DEBUG - Erreur: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": str(e)
            })
    
    print("DEBUG - Méthode non autorisée")
    return JsonResponse({"success": False, "error": "Méthode non autorisée"})

@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk, entreprise=request.user.entreprise)
    
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client mis à jour")
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'vente/client_form.html', {'form': form})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk, entreprise=request.user.entreprise)
    ventes = Vente.objects.filter(client=client).order_by('-date')
    
    context = {
        'client': client,
        'ventes': ventes,
        'total_achats': ventes.aggregate(Sum('total'))['total__sum'] or 0,
    }
    
    return render(request, 'vente/client_detail.html', context)

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, entreprise=request.user.entreprise)
    
    if request.method == "POST":
        client.delete()
        messages.success(request, "Client supprimé")
        return redirect('client_list')
    
    return render(request, 'vente/client_confirm_delete.html', {'client': client})

# ============================================
# VUES AJAX/UTILITAIRES
# ============================================

@login_required
def check_stock(request, produit_id):
    """
    Vérifie le stock disponible pour un produit (AJAX).
    """
    try:
        produit = Produit.objects.get(id=produit_id)
        
        if not request.user.est_super_admin and produit.entreprise != request.user.entreprise:
            return JsonResponse({
                "success": False,
                "error": "Accès non autorisé"
            }, status=403)
        
        try:
            stock = Stock.objects.get(produit=produit, entreprise=request.user.entreprise)
            stock_disponible = stock.quantite
        except Stock.DoesNotExist:
            stock_disponible = 0
        
        return JsonResponse({
            "success": True,
            "produit_id": produit.id,
            "nom": produit.nom,
            "stock_disponible": stock_disponible,
            "prix": float(produit.prix_vente_detail)
        })
        
    except Produit.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Produit non trouvé"
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

@login_required
def export_ventes(request):
    """
    Export des ventes en CSV/Excel.
    """
    user = request.user
    queryset = Vente.objects.all()
    
    if not user.est_super_admin:
        queryset = queryset.filter(entreprise=user.entreprise)
    
    # Appliquer les mêmes filtres que la liste
    period = request.GET.get('period')
    if period == 'today':
        queryset = queryset.filter(date__date=timezone.now().date())
    elif period == 'week':
        week_ago = timezone.now() - timedelta(days=7)
        queryset = queryset.filter(date__gte=week_ago)
    elif period == 'month':
        month_ago = timezone.now() - timedelta(days=30)
        queryset = queryset.filter(date__gte=month_ago)
    
    client_id = request.GET.get('client')
    if client_id:
        queryset = queryset.filter(client_id=client_id)
    
    format_type = request.GET.get('format', 'csv')
    
    import csv
    from django.http import HttpResponse
    
    if format_type == 'excel':
        import xlwt
        
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="ventes.xls"'
        
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Ventes')
        
        # En-tête
        headers = ['ID', 'Date', 'Client', 'Total (FCFA)', 'Articles', 'Vendeur']
        for col_num, header in enumerate(headers):
            ws.write(0, col_num, header)
        
        # Données
        for row_num, vente in enumerate(queryset, 1):
            ws.write(row_num, 0, vente.id)
            ws.write(row_num, 1, vente.date.strftime('%d/%m/%Y %H:%M'))
            ws.write(row_num, 2, vente.client.nom if vente.client else 'Comptant')
            ws.write(row_num, 3, str(vente.total))
            ws.write(row_num, 4, vente.lignes.count())
            ws.write(row_num, 5, vente.utilisateur.get_full_name() or vente.utilisateur.username)
        
        wb.save(response)
        return response
        
    else:  # CSV par défaut
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ventes.csv"'
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['ID', 'Date', 'Client', 'Total (FCFA)', 'Articles', 'Vendeur'])
        
        for vente in queryset:
            writer.writerow([
                vente.id,
                vente.date.strftime('%d/%m/%Y %H:%M'),
                vente.client.nom if vente.client else 'Comptant',
                str(vente.total),
                vente.lignes.count(),
                vente.utilisateur.get_full_name() or vente.utilisateur.username
            ])
        
        return response

# ============================================
# VUES DASHBOARD/STATISTIQUES
# ============================================

@login_required
def dashboard(request):
    """
    Tableau de bord avec statistiques des ventes.
    """
    user = request.user
    today = timezone.now().date()
    
    # Ventes du jour
    ventes_today = Vente.objects.filter(
        entreprise=user.entreprise,
        date__date=today
    ) if not user.est_super_admin else Vente.objects.filter(date__date=today)
    
    # Statistiques
    total_ventes_jour = ventes_today.count()
    ca_jour = ventes_today.aggregate(Sum('total'))['total__sum'] or 0
    
    # Ventes de la semaine
    week_start = today - timedelta(days=today.weekday())
    ventes_semaine = Vente.objects.filter(
        entreprise=user.entreprise,
        date__date__gte=week_start
    ) if not user.est_super_admin else Vente.objects.filter(date__date__gte=week_start)
    
    total_ventes_semaine = ventes_semaine.count()
    ca_semaine = ventes_semaine.aggregate(Sum('total'))['total__sum'] or 0
    
    # Meilleurs produits du mois
    month_start = today.replace(day=1)
    meilleurs_produits = LigneVente.objects.filter(
        vente__date__gte=month_start,
        vente__entreprise=user.entreprise
    ).values('produit__nom').annotate(
        total_vendu=Sum('quantite'),
        total_ca=Sum('total')
    ).order_by('-total_vendu')[:5]
    
    # Dernières ventes
    dernieres_ventes = Vente.objects.filter(
        entreprise=user.entreprise
    ).order_by('-date')[:10] if not user.est_super_admin else Vente.objects.order_by('-date')[:10]
    
    context = {
        'total_ventes_jour': total_ventes_jour,
        'ca_jour': ca_jour,
        'total_ventes_semaine': total_ventes_semaine,
        'ca_semaine': ca_semaine,
        'meilleurs_produits': meilleurs_produits,
        'dernieres_ventes': dernieres_ventes,
    }
    
    return render(request, 'vente/dashboard.html', context)