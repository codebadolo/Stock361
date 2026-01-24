# fournisseur/models.py
from django.db import models
from entreprise.models import Entreprise
from produit.models import Produit
from django.utils import timezone

class Fournisseur(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='fournisseurs')
    nom = models.CharField(max_length=150)
    contact = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.nom

class Approvisionnement(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True)
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True)
    quantite = models.PositiveIntegerField()
    prix_achat = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.produit.nom} - {self.quantite}"
