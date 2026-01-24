from django.db import models
from entreprise.models import Entreprise
from django.utils import timezone
from django.utils.text import slugify
import uuid

# ===================== CATEGORIES =====================
class Categorie(models.Model):
    entreprise = models.ForeignKey(
        'entreprise.Entreprise', 
        on_delete=models.CASCADE, 
        related_name='categories'
    )
    nom = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sous_categories'
    )

    def __str__(self):
        full_name = self.nom
        if self.parent:
            full_name = f"{self.parent.nom} > {self.nom}"
        return full_name

# ===================== PRODUITS =====================
class Produit(models.Model):
    entreprise = models.ForeignKey(
        'entreprise.Entreprise',
        on_delete=models.CASCADE,
        related_name='produits'
    )
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='produits'
    )
    reference = models.CharField(max_length=50, unique=True, editable=False)
    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    prix_achat = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    prix_vente_detail = models.DecimalField(max_digits=12, null=True ,decimal_places=2)
    prix_vente_gros = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    stock_minimum = models.PositiveIntegerField(default=0)
    est_actif = models.BooleanField(default=True)
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.reference})"

    # Générer automatiquement une référence unique avant sauvegarde
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)

    def generate_reference(self):
        """
        Génère une référence unique automatique sous la forme :
        NOMCOURT-UUID4[:8] ex: PRODABC-1a2b3c4d
        """
        base = slugify(self.nom)[:6].upper()
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"{base}-{unique_id}"

    @property
    def etat_stock(self):
        """
        Retourne l'état du stock par rapport au stock minimum :
        - 'rupture' si 0
        - 'critique' si inférieur au stock_minimum
        - 'normal' sinon
        """
        try:
            stock = self.stock.quantite
        except:
            stock = 0

        if stock == 0:
            return 'rupture'
        elif stock < self.stock_minimum:
            return 'critique'
        else:
            return 'normal'
