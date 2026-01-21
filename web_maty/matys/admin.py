from django.contrib import admin
from .models import Prenda
import json

@admin.register(Prenda)
class PrendaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'tipo', 'precio', 'disponible')
    list_filter = ('categoria', 'tipo', 'disponible','colores_disponibles')
    search_fields = ('nombre', 'descripcion_corta')
    prepopulated_fields = {'slug': ('nombre',)}
    list_editable = ('disponible',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'categoria', 'tipo', 'precio')
        }),
        ('Descripción', {
            'fields': ('descripcion_corta', 'descripcion_larga')
        }),
        ('Especificaciones', {
            'fields': ('material', 'largo', 'cuidado')
        }),
        ('Disponibilidad', {
            'fields': ('disponible', 'tallas_disponibles')
        }),
        ('Imágenes', {
            'fields': ('imagen_principal', 'imagen_2', 'imagen_3', 'imagen_4')
        }),
    )