from django.urls import path
from . import views

urlpatterns = [
    path('stocks/', views.StockListView.as_view(), name='stock_list'),
    path('mouvements/', views.MouvementStockListView.as_view(), name='mouvement_list'),
    path('mouvements/nouveau/', views.ajouter_mouvement, name='mouvement_create'),
    path('inventaires/', views.InventaireListView.as_view(), name='inventaire_list'),
    path('inventaires/nouveau/', views.creer_inventaire, name='inventaire_create'),
    path('inventaires/<int:pk>/', views.detail_inventaire, name='inventaire_detail'),
    path('get-stock-data/', views.get_stock_data, name='get_stock_data'),
    path('mouvements/ajouter-ajax/', views.ajouter_mouvement_ajax, name='ajouter_mouvement_ajax'),
]
