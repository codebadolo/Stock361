# fournisseur/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import Fournisseur, Approvisionnement
from .forms import FournisseurForm, ApprovisionnementForm
from stock.models import Stock, MouvementStock


# ===================== FOURNISSEURS =====================
class FournisseurListView(LoginRequiredMixin, ListView):
    model = Fournisseur
    template_name = 'fournisseur/fournisseur_list.html'
    context_object_name = 'fournisseurs'

    def get_queryset(self):
        return Fournisseur.objects.filter(entreprise=self.request.user.entreprise)


class FournisseurCreateView(LoginRequiredMixin, CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'fournisseur/fournisseur_form.html'
    success_url = reverse_lazy('fournisseur_list')

    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        messages.success(self.request, "Fournisseur ajouté avec succès")
        return super().form_valid(form)


class FournisseurUpdateView(LoginRequiredMixin, UpdateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'fournisseur/fournisseur_form.html'
    success_url = reverse_lazy('fournisseur_list')


# ===================== APPROVISIONNEMENTS =====================
class ApprovisionnementListView(LoginRequiredMixin, ListView):
    model = Approvisionnement
    template_name = 'fournisseur/approvisionnement_list.html'
    context_object_name = 'approvisionnements'
    paginate_by = 20

    def get_queryset(self):
        return Approvisionnement.objects.filter(
            entreprise=self.request.user.entreprise
        ).select_related('produit', 'fournisseur').order_by('-date')


def ajouter_approvisionnement(request):
    if request.method == 'POST':
        form = ApprovisionnementForm(request.POST)
        if form.is_valid():
            appro = form.save(commit=False)
            appro.entreprise = request.user.entreprise
            appro.save()

            # Mise à jour du stock
            stock, _ = Stock.objects.get_or_create(
                entreprise=request.user.entreprise,
                produit=appro.produit,
                defaults={'quantite': 0}
            )
            avant = stock.quantite
            stock.quantite += appro.quantite
            stock.save()

            # Historique mouvement
            MouvementStock.objects.create(
                entreprise=request.user.entreprise,
                produit=appro.produit,
                type_mouvement='entree',
                quantite=appro.quantite,
                avant=avant,
                apres=stock.quantite,
                utilisateur=request.user,
                commentaire=f"Approvisionnement via {appro.fournisseur.nom}"
            )

            messages.success(request, "Approvisionnement enregistré et stock mis à jour.")
            return redirect('approvisionnement_list')
    else:
        form = ApprovisionnementForm()

    return render(request, 'fournisseur/approvisionnement_form.html', {
        'form': form
    })
