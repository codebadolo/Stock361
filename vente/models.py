from django.db import models
from entreprise.models import Entreprise, Utilisateur
from produit.models import Produit
from django.utils import timezone

class Client(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='clients')
    nom = models.CharField(max_length=150)
    contact = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.nom

class Vente(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recu_pdf = models.FileField(upload_to='recu_vente/', blank=True, null=True)

    def __str__(self):
        return f"Vente #{self.id} - {self.total}"

class LigneVente(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.produit.nom} x {self.quantite}"
