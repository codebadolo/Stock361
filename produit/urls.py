from django.urls import path
from . import views

app_name = 'produit'

urlpatterns = [
    # Produits - Views principales
    path('produits/', views.ProduitListView.as_view(), name='produit_list'),
    path('detail/<int:pk>/', views.ProduitDetailView.as_view(), name='produit_detail'),
    
    # Produits - API AJAX
    path('produits/<int:pk>/detail-json/', views.produit_detail_json, name='produit_detail_json'),
    path('produits/nouveau/', views.produit_create_ajax, name='produit_create_modal'),
    path('produits/<int:pk>/modifier/', views.produit_update_ajax, name='produit_update_modal'),
    path('produits/<int:pk>/supprimer/', views.produit_delete_ajax, name='produit_delete_modal'),
    
    # Export
    path('export/excel/', views.export_produits_excel, name='export_produits_excel'),
    
    # Catégories
    path('categories/', views.CategorieListView.as_view(), name='categorie_list'),
    path('categorie/create/', views.categorie_create_ajax, name='categorie_create_ajax'),
    path('categorie/<int:pk>/update/', views.categorie_update_ajax, name='categorie_update_ajax'),
]