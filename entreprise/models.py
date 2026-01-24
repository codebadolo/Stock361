# entreprise/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Entreprise(models.Model):
    nom = models.CharField(max_length=150)
    ifu = models.CharField(max_length=50, unique=True)
    contact = models.CharField(max_length=50, blank=True, null=True)
    logo = models.ImageField(upload_to='entreprises/logos/', blank=True, null=True)
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nom


class Utilisateur(AbstractUser):
    """
    Modèle utilisateur personnalisé
    """
    class TypeUtilisateur(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        RESPONSABLE = 'responsable', 'Responsable'
        GERANT = 'gerant', 'Gérant/Secrétaire'

    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name='utilisateurs',
        blank=True,
        null=True
    )
    type_utilisateur = models.CharField(
        max_length=20,
        choices=TypeUtilisateur.choices,
        default=TypeUtilisateur.GERANT
    )
    est_actif = models.BooleanField(default=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.username} ({self.get_type_utilisateur_display()})"

    # Propriétés pratiques
    @property
    def est_super_admin(self):
        return self.type_utilisateur == self.TypeUtilisateur.SUPER_ADMIN

    @property
    def est_responsable(self):
        return self.type_utilisateur == self.TypeUtilisateur.RESPONSABLE

    @property
    def est_gerant(self):
        return self.type_utilisateur == self.TypeUtilisateur.GERANT

    def get_role_display(self):
        """
        Retourne le rôle lisible (Super Admin, Responsable, Gérant/Secrétaire)
        """
        return self.get_type_utilisateur_display()    
    @property
    def responsable(self):
        """
        Retourne le premier utilisateur de type 'responsable' ou None
        """
        return self.utilisateurs.filter(type_utilisateur='responsable').first()
# entreprise/forms.py