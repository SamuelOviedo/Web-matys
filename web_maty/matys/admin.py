from django.contrib import admin
from .models import Prenda
import json

@admin.register(Prenda)
class PrendaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'tipo', 'precio','destacada', 'disponible')
    list_filter = ('categoria', 'tipo','destacada', 'disponible')
    search_fields = ('nombre', 'descripcion_corta')
    prepopulated_fields = {'slug': ('nombre',)}
    list_editable = ('disponible','destacada')
    
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
            'fields': ('disponible','destacada', 'tallas_disponibles')
        }),
        ('Imágenes', {
            'fields': ('imagen_principal', 'imagen_2', 'imagen_3', 'imagen_4')
        }),
    )