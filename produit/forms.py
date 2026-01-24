from django import forms
from .models import Produit, Categorie

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = [
            'categorie', 'nom', 'description', 'prix_achat',
            'prix_vente_detail', 'prix_vente_gros', 'stock_minimum',
            'image', 'est_actif'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'est_actif': forms.CheckboxInput(attrs={'class': 'form-input'}),
        }


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom', 'parent']
