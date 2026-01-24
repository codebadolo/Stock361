# entreprise/urls.py
from django.urls import path
from . import views
from django.views.generic import RedirectView
urlpatterns = [
     path('', RedirectView.as_view(pattern_name='login', permanent=False)),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Entreprises
    path('entreprises/', views.EntrepriseListView.as_view(), name='entreprise_list'),
    path('entreprises/nouveau/', views.EntrepriseCreateView.as_view(), name='entreprise_create'),
    path('entreprises/<int:pk>/modifier/', views.EntrepriseUpdateView.as_view(), name='entreprise_update'),

    # Utilisateurs
    path('utilisateurs/', views.UtilisateurListView.as_view(), name='utilisateur_list'),
    
    path('utilisateurs/nouveau/', views.UtilisateurCreateView.as_view(), name='utilisateur_create'),
    path('<int:pk>/', views.UtilisateurDetailView.as_view(), name='utilisateur_detail'),
 path('utilisateurs/<int:pk>/modifier/', views.UtilisateurUpdateView.as_view(), name='utilisateur_update'),
     path('entreprises/<int:pk>/', views.EntrepriseDetailView.as_view(), name='entreprise_detail'),

    path('utilisateurs/<int:pk>/supprimer/', views.UtilisateurDeleteView.as_view(), name='utilisateur_delete'),
    # Profil et mot de passe
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/changer-mot-de-passe/', views.change_password, name='change_password'),
]
