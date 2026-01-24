# fournisseur/forms.py
from django import forms
from .models import Fournisseur, Approvisionnement

class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'contact']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du fournisseur'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone / Email'
            }),
        }


class ApprovisionnementForm(forms.ModelForm):
    class Meta:
        model = Approvisionnement
        fields = ['fournisseur', 'produit', 'quantite', 'prix_achat']
        widgets = {
            'fournisseur': forms.Select(attrs={'class': 'form-select'}),
            'produit': forms.Select(attrs={'class': 'form-select'}),
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'prix_achat': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }
