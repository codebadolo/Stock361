from django.db import models
from entreprise.models import Entreprise, Utilisateur
from produit.models import Produit
from django.utils import timezone

# Stock actuel des produits
class Stock(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='stocks')
    produit = models.OneToOneField(Produit, on_delete=models.CASCADE, related_name='stock')
    quantite = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.produit.nom} - {self.quantite}"


# Historique des mouvements
class MouvementStock(models.Model):
    class TypeMouvement(models.TextChoices):
        ENTREE = 'entree', 'Entrée'
        SORTIE = 'sortie', 'Sortie'
        AJUSTEMENT = 'ajustement', 'Ajustement'

    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    type_mouvement = models.CharField(max_length=20, choices=TypeMouvement.choices)
    quantite = models.IntegerField()
    avant = models.IntegerField()
    apres = models.IntegerField()
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    commentaire = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.type_mouvement} - {self.produit.nom} ({self.quantite})"


# Inventaire physique
class Inventaire(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='inventaires')
    date = models.DateTimeField(default=timezone.now)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    commentaire = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Inventaire {self.id} - {self.date.strftime('%Y-%m-%d')}"

# Détail de l’inventaire : quantité comptée vs quantité théorique
class LigneInventaire(models.Model):
    inventaire = models.ForeignKey(Inventaire, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite_theorique = models.IntegerField()
    quantite_comptee = models.IntegerField()
    ecart = models.IntegerField()  # Calculé : quantite_comptee - quantite_theorique

    def save(self, *args, **kwargs):
        # Calcul automatique de l’écart
        self.ecart = self.quantite_comptee - self.quantite_theorique
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produit.nom} - Théorique: {self.quantite_theorique}, Comptée: {self.quantite_comptee}"
