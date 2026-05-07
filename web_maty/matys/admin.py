from django.contrib import admin
from django.utils.html import format_html
import cloudinary

from .models import Prenda, ImagenPrenda


class ImagenPrendaInline(admin.StackedInline):
    model = ImagenPrenda
    extra = 1
    max_num = 4
    fields = ('imagen', 'preview', 'orden')
    readonly_fields = ('preview',)
    ordering = ('orden',)

    def preview(self, obj):
        if obj.pk and obj.imagen:
            url = cloudinary.CloudinaryImage(str(obj.imagen)).build_url(
                width=150, crop='scale'
            )
            return format_html(
                '<img src="{}" style="max-height:150px; border-radius:4px;" />', url
            )
        return '—'
    preview.short_description = 'Vista previa'


@admin.register(Prenda)
class PrendaAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'nombre', 'categoria', 'tipo', 'precio', 'destacada', 'disponible')
    list_filter = ('categoria', 'tipo', 'destacada', 'disponible')
    search_fields = ('nombre', 'descripcion_corta')
    prepopulated_fields = {'slug': ('nombre',)}
    list_editable = ('disponible', 'destacada')
    inlines = [ImagenPrendaInline]

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
            'fields': ('disponible', 'destacada', 'tallas_disponibles', 'colores_disponibles')
        }),
    )

    def thumbnail(self, obj):
        img = obj.imagenes.filter(orden=0).first()
        if img and img.imagen:
            url = cloudinary.CloudinaryImage(str(img.imagen)).build_url(
                width=60, height=60, crop='fill'
            )
            return format_html(
                '<img src="{}" style="height:60px; width:60px; object-fit:cover; border-radius:4px;" />', url
            )
        return '—'
    thumbnail.short_description = 'Imagen'
