# vente/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ============================================
    # VENTES
    # ============================================
    path('', views.VenteListView.as_view(), name='vente_list'),
    path('nouvelle/', views.vente_create, name='vente_create'),
    path('<int:pk>/', views.vente_detail, name='vente_detail'),
    path('<int:pk>/supprimer/', views.vente_delete, name='vente_delete'),
    
    # ============================================
    # RECUS PDF
    # ============================================
    path('<int:pk>/generer-recu/', views.generate_receipt, name='generate_receipt'),
    path('<int:pk>/telecharger-recu/', views.download_receipt, name='download_receipt'),
    path('<int:pk>/voir-recu/', views.view_receipt, name='view_receipt'),
    path('<int:pk>/generer-document/', views.generate_document, name='generate_document'),
    path('<int:pk>/generer-facture/', views.generate_receipt, {'doc_type': 'invoice'}, name='generate_invoice'),
    path('<int:pk>/voir-document/', views.view_receipt, name='view_receipt'),
    path('<int:pk>/voir-document/<str:doc_type>/', views.view_receipt, name='view_document_type'),
    # ============================================
    # CLIENTS
    # ============================================
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/nouveau/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/modifier/', views.client_update, name='client_update'),
    path('clients/<int:pk>/supprimer/', views.client_delete, name='client_delete'),
    path('clients/create-ajax/', views.client_create_ajax, name='client_create_ajax'),
    
    # ============================================
    # AJAX & UTILITAIRES
    # ============================================
    path('check-stock/<int:produit_id>/', views.check_stock, name='check_stock'),
    path('export/', views.export_ventes, name='export_ventes'),
    
    # ============================================
    # DASHBOARD
    # ============================================
    path('dashboard/', views.dashboard, name='dashboard_ventes'),
]