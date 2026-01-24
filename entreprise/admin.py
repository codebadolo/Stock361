from django.contrib import admin

# Register your models here.
from .models import Entreprise,Utilisateur

admin.site.register(Entreprise)
admin.site.register(Utilisateur)