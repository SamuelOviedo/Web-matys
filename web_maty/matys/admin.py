from django.contrib import admin
from django.utils.html import format_html
import cloudinary

from .models import Prenda, ImagenPrenda, TipoPrenda, SiteConfig


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    """Respaldo de emergencia: los textos se editan normalmente en /gestion-matys/inicio/."""
    list_display = ('__str__', 'actualizado')

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class ImagenPrendaInline(admin.StackedInline):
    model = ImagenPrenda
    verbose_name = 'Foto'
    verbose_name_plural = 'Fotos de la prenda  ·  máximo 4  ·  la foto con orden 0 aparece en el catálogo'
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
    readonly_fields = ('thumbnail',)
    inlines = [ImagenPrendaInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('thumbnail', 'nombre', 'slug', 'categoria', 'tipo', 'precio'),
            'description': 'La foto principal se gestiona desde la sección "Fotos" al final del formulario.',
        }),
        ('Descripción', {
            'fields': ('descripcion_corta', 'descripcion_larga'),
        }),
        ('Especificaciones', {
            'fields': ('material', 'largo', 'cuidado'),
        }),
        ('Disponibilidad y Variantes', {
            'fields': ('disponible', 'destacada', 'tallas_disponibles', 'colores_disponibles'),
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
        return format_html('<span style="color:#aaa;font-size:12px;">Sin imagen</span>')
    thumbnail.short_description = 'Foto'

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        imagenes = list(form.instance.imagenes.order_by('orden'))
        for i, img in enumerate(imagenes):
            if img.orden != i:
                img.orden = i
                img.save(update_fields=['orden'])


@admin.register(TipoPrenda)
class TipoPrendaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'activo', 'orden']
    list_filter = ['categoria', 'activo']
    list_editable = ['activo', 'orden']
    prepopulated_fields = {'slug': ('nombre',)}
