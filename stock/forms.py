from django import forms
from .models import Stock, MouvementStock, Inventaire, LigneInventaire
from produit.models import Produit

class MouvementStockForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['produit', 'type_mouvement', 'quantite', 'commentaire']

class InventaireForm(forms.ModelForm):
    class Meta:
        model = Inventaire
        fields = ['commentaire']

class LigneInventaireForm(forms.ModelForm):
    class Meta:
        model = LigneInventaire
        fields = ['produit', 'quantite_comptee']
        widgets = {
            'quantite_comptee': forms.NumberInput(attrs={'min':0}),
        }
