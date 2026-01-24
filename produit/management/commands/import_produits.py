# produit/management/commands/import_produits.py
import os
import openpyxl
from django.core.management.base import BaseCommand
from produit.models import Produit, Categorie
from entreprise.models import Entreprise

class Command(BaseCommand):
    help = "Importe des produits depuis le fichier Excel produit_wendpanga.xlsx pour l’entreprise WEND PANGA"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Chemin du fichier Excel à importer (optionnel, défaut: produit_wendpanga.xlsx)'
        )

    def handle(self, *args, **options):
        # Chemin par défaut : même dossier que cette commande
        default_path = os.path.join(os.path.dirname(__file__), 'produit_wendpanga.xlsx')
        file_path = options.get('file') or default_path

        # Vérification que le fichier existe
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Fichier Excel introuvable : {file_path}"))
            return

        try:
            wb = openpyxl.load_workbook(file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Impossible d’ouvrir le fichier Excel : {e}"))
            return

        sheet = wb.active

        # Récupérer l'entreprise WEND PANGA
        try:
            entreprise = Entreprise.objects.get(nom__iexact="WEND PANGA")
        except Entreprise.DoesNotExist:
            self.stdout.write(self.style.ERROR("Entreprise 'WEND PANGA' introuvable dans la base de données"))
            return

        success_count = 0
        skip_count = 0

        # Supposons que la première ligne est l'en-tête : Référence | Produit | Catégorie
        for row in sheet.iter_rows(min_row=2, values_only=True):
            reference, nom_produit, nom_categorie = row

            if not nom_produit:
                continue

            # Récupérer ou créer la catégorie
            categorie_obj = None
            if nom_categorie:
                categorie_obj, _ = Categorie.objects.get_or_create(
                    entreprise=entreprise,
                    nom=nom_categorie
                )

            # Vérifier si le produit existe déjà pour cette entreprise
            produit, created = Produit.objects.get_or_create(
                reference=reference,
                entreprise=entreprise,
                defaults={
                    'nom': nom_produit,
                    'categorie': categorie_obj
                }
            )

            if created:
                success_count += 1
            else:
                skip_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import terminé : {success_count} produits ajoutés, {skip_count} produits existants ignorés"
        ))
