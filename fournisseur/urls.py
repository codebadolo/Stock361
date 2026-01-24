# fournisseur/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Fournisseurs
    path('fournisseurs/', views.FournisseurListView.as_view(), name='fournisseur_list'),
    path('fournisseurs/nouveau/', views.FournisseurCreateView.as_view(), name='fournisseur_create'),
    path('fournisseurs/<int:pk>/modifier/', views.FournisseurUpdateView.as_view(), name='fournisseur_update'),

    # Approvisionnements
    path('approvisionnements/', views.ApprovisionnementListView.as_view(), name='approvisionnement_list'),
    path('approvisionnements/nouveau/', views.ajouter_approvisionnement, name='approvisionnement_create'),
]
