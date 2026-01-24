# entreprise/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Utilisateur, Entreprise
from django.forms import inlineformset_factory
from produit.models import Produit
class UtilisateurCreationForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = [
            'username', 'first_name', 'last_name', 'email', 
            'type_utilisateur', 'entreprise', 'telephone', 'adresse', 
            'password1', 'password2'
        ]

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email', 'telephone', 'adresse']

class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = ['nom', 'ifu', 'contact', 'logo', 'est_actif']

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur

# ----------------- Création -----------------
class UtilisateurCreationForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'entreprise', 'type_utilisateur', 'telephone', 'adresse'
        ]

# ----------------- Mise à jour -----------------
class UtilisateurUpdateForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'entreprise', 'type_utilisateur', 'telephone', 'adresse', 'est_actif'
        ]
        widgets = {
            'type_utilisateur': forms.Select(attrs={'class': 'form-select'}),
            'entreprise': forms.Select(attrs={'class': 'form-select'}),
        }
