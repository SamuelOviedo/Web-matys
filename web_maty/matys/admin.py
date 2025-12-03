from django.contrib import admin
from .models import Prenda

@admin.register(Prenda)
class PrendaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'tipo', 'precio', 'disponible')
    list_filter = ('categoria', 'tipo', 'disponible')
    search_fields = ('nombre', 'descripcion_corta')
    prepopulated_fields = {'slug': ('nombre',)}
    list_editable = ('disponible',)