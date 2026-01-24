from django import forms
from django.forms import inlineformset_factory
from .models import Vente, LigneVente, Client
from produit.models import Produit

# ---------------- CLIENT ----------------
class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'contact']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du client'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone / Contact'
            }),
        }


# ---------------- VENTE ----------------
class VenteForm(forms.ModelForm):
    class Meta:
        model = Vente
        fields = ['client']
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


# ---------------- LIGNE DE VENTE ----------------
class LigneVenteForm(forms.ModelForm):
    class Meta:
        model = LigneVente
        fields = ['produit', 'quantite', 'prix_unitaire']
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-select'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        if entreprise:
            self.fields['produit'].queryset = Produit.objects.filter(
                entreprise=entreprise,
                est_actif=True
            )


# ---------------- FORMSET POUR LES LIGNES ----------------
LigneVenteFormSet = inlineformset_factory(
    Vente,
    LigneVente,
    form=LigneVenteForm,
    extra=1,
    can_delete=True
)
