# entreprise/views.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import UpdateView, DeleteView
from .models import Utilisateur
from .forms import UtilisateurCreationForm, UtilisateurUpdateForm
class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.est_super_admin
class ResponsableOrSuperAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.est_super_admin or self.request.user.est_responsable
class ResponsableRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.est_super_admin or self.request.user.est_responsable
        )

class GerantRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated

# entreprise/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .models import Entreprise, Utilisateur
from .forms import UtilisateurCreationForm, ProfileUpdateForm, EntrepriseForm
from django.utils import timezone
from datetime import timedelta

# --- Authentification ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            if user.est_actif:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Compte désactivé.")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    
    return render(request, 'entreprise/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Déconnecté avec succès.")
    return redirect('login')

# --- Dashboard ---
# views.py - version simplifiée
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from entreprise.models import Entreprise
from produit.models import Produit
from vente.models import Vente, LigneVente
from stock.models import MouvementStock

@login_required
def dashboard_view(request):
    context = {}
    user = request.user
    entreprise = user.entreprise if hasattr(user, 'entreprise') else None
    aujourdhui = timezone.now().date()
    debut_semaine = aujourdhui - timedelta(days=aujourdhui.weekday())
    
    context.update({
        'aujourdhui': aujourdhui,
        'user': user,
        'entreprise': entreprise,
    })
    
    # Pour Super Admin
    if user.est_super_admin:
        context.update({
            'dashboard_type': 'super_admin',
            'total_entreprises': Entreprise.objects.count(),
            'total_utilisateurs': user.__class__.objects.count(),
        })
    
    # Pour Responsable
    elif user.est_responsable and entreprise:
        context.update({
            'dashboard_type': 'responsable',
            'total_utilisateurs': entreprise.utilisateurs.count(),
            'total_produits': Produit.objects.filter(entreprise=entreprise).count(),
        })
    
    # Pour Gérant (version simplifiée)
    elif user.est_gerant and entreprise:
        # Statistiques de base pour gérant
        ventes_aujourdhui = Vente.objects.filter(
            entreprise=entreprise,
            utilisateur=user,
            date__date=aujourdhui
        )
        
        ventes_semaine = Vente.objects.filter(
            entreprise=entreprise,
            utilisateur=user,
            date__date__gte=debut_semaine
        )
        
        ca_aujourdhui = ventes_aujourdhui.aggregate(total=Sum('total'))['total'] or 0
        ca_semaine = ventes_semaine.aggregate(total=Sum('total'))['total'] or 0
        
        # Produits en stock faible
        produits_faible_stock = Produit.objects.filter(
            entreprise=entreprise,
             # Exemple: moins de 10 unités
        )[:5]
        
        # Dernières ventes
        dernieres_ventes = Vente.objects.filter(
            entreprise=entreprise,
            utilisateur=user
        ).order_by('-date')[:5]
        
        # Mouvements récents
        mouvements_recents = MouvementStock.objects.filter(
            entreprise=entreprise
        ).order_by('-date')[:5]
        
        context.update({
            'dashboard_type': 'gerant',
            'ventes_aujourdhui': ventes_aujourdhui.count(),
            'ventes_semaine': ventes_semaine.count(),
            'ca_aujourdhui': ca_aujourdhui,
            'ca_semaine': ca_semaine,
            'produits_faible_stock': produits_faible_stock,
            'dernieres_ventes': dernieres_ventes,
            'mouvements_recents': mouvements_recents,
        })
    
    return render(request, 'entreprise/dashboard.html', context)

# --- Entreprises ---
class EntrepriseListView(SuperAdminRequiredMixin, ListView):
    model = Entreprise
    template_name = 'entreprise/entreprise_list.html'
    context_object_name = 'entreprises'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprises = context['entreprises']

        context['total_entreprises'] = entreprises.count()
        context['total_actives'] = entreprises.filter(est_actif=True).count()
        context['total_inactives'] = entreprises.filter(est_actif=False).count()
        return context
# entreprise/views.py
from django.views.generic import DetailView

class EntrepriseDetailView(SuperAdminRequiredMixin, DetailView):
    model = Entreprise
    template_name = 'entreprise/entreprise_detail.html'
    context_object_name = 'entreprise'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.object
        utilisateurs = entreprise.utilisateurs.all()
        context['utilisateurs'] = utilisateurs
        # Stats par rôle
        context['total_super_admin'] = utilisateurs.filter(type_utilisateur='super_admin').count()
        context['total_responsable'] = utilisateurs.filter(type_utilisateur='responsable').count()
        context['total_gerant'] = utilisateurs.filter(type_utilisateur='gerant').count()
        context['total_utilisateurs'] = utilisateurs.count()
        return context


class EntrepriseCreateView(SuperAdminRequiredMixin, CreateView):
    model = Entreprise
    form_class = EntrepriseForm
    template_name = 'entreprise/entreprise_form.html'
    success_url = reverse_lazy('entreprise_list')

class EntrepriseUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Entreprise
    form_class = EntrepriseForm
    template_name = 'entreprise/entreprise_form.html'
    success_url = reverse_lazy('entreprise_list')

# --- Utilisateurs ---
class UtilisateurListView(ResponsableRequiredMixin, ListView):
    model = Utilisateur
    template_name = 'entreprise/utilisateur_list.html'
    context_object_name = 'utilisateurs'
    
    def get_queryset(self):
        user = self.request.user
        if user.est_super_admin:
            return Utilisateur.objects.all()
        return Utilisateur.objects.filter(entreprise=user.entreprise)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        utilisateurs = context['utilisateurs']
        context['total_utilisateurs'] = utilisateurs.count()
        context['total_super_admin'] = utilisateurs.filter(type_utilisateur='super_admin').count()
        context['total_responsable'] = utilisateurs.filter(type_utilisateur='responsable').count()
        context['total_gerant'] = utilisateurs.filter(type_utilisateur='gerant').count()
        return context

class UtilisateurCreateView(ResponsableRequiredMixin, CreateView):
    model = Utilisateur
    form_class = UtilisateurCreationForm
    template_name = 'entreprise/utilisateur_form.html'
    success_url = reverse_lazy('utilisateur_list')

    def form_valid(self, form):
        if not self.request.user.est_super_admin:
            form.instance.entreprise = self.request.user.entreprise
        return super().form_valid(form)

class UtilisateurUpdateView(ResponsableOrSuperAdminMixin, LoginRequiredMixin, UpdateView):
    model = Utilisateur
    form_class = UtilisateurUpdateForm
    template_name = 'entreprise/utilisateur_form.html'
    success_url = reverse_lazy('utilisateur_list')

    def form_valid(self, form):
        # Si l'utilisateur n'est pas super admin, on verrouille l'entreprise
        if not self.request.user.est_super_admin:
            form.instance.entreprise = self.request.user.entreprise
        messages.success(self.request, "Utilisateur mis à jour avec succès !")
        return super().form_valid(form)

# ------------------ Delete Utilisateur ------------------
class UtilisateurDeleteView(SuperAdminRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Utilisateur
    template_name = 'entreprise/utilisateur_confirm_delete.html'
    success_url = reverse_lazy('entreprise:utilisateur_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Utilisateur supprimé avec succès !")
        return super().delete(request, *args, **kwargs)

class UtilisateurDetailView(ResponsableRequiredMixin, DetailView):
    model = Utilisateur
    template_name = 'entreprise/utilisateur_detail.html'
    context_object_name = 'utilisateur'

    def get_queryset(self):
        user = self.request.user
        if user.est_super_admin:
            return Utilisateur.objects.all()
        return Utilisateur.objects.filter(entreprise=user.entreprise)        
class ProfileView(UpdateView):
    model = Utilisateur
    form_class = ProfileUpdateForm
    template_name = 'entreprise/profile.html'
    
    def get_object(self):
        return self.request.user
    
    def get_success_url(self):
        return reverse_lazy('profile')

@login_required
def change_password(request):
    from django.contrib.auth.forms import PasswordChangeForm
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Mot de passe changé avec succès!")
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'entreprise/change_password.html', {'form': form})
