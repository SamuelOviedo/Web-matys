from django.db import models
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField


class Prenda(models.Model):
    CATEGORIAS = [
    ('femenino',  'Femenino'),
    ('masculino', 'Masculino'),
    ('infantil',  'Infantil'),
    ]

    TIPOS = [
        # ── Femenino › Vestidos ──────────────────
        ('vestido_gala',       'Vestido de gala'),
        ('vestido_casual',     'Vestido casual'),
        ('vestido_semiformal', 'Vestido semiformal'),
        ('vestido_novia',      'Vestido de novia'),
        ('vestido_quince',     'Vestido de quinceañera'),
        ('vestido_alusivo',    'Vestido alusivo'),
        ('vestido_playero',    'Vestido playero'),
    # ── Femenino › Otros ─────────────────────
        ('blusa',              'Blusa'),
        ('falda',              'Falda'),
        ('chaleco',            'Chaleco'),
        ('pantalon',           'Pantalón'),
        ('traje',              'Traje'),
        ('traje_alusivo',      'Traje alusivo'),
    # ── Masculino ────────────────────────────
        ('sueter',             'Suéter'),
        ('camisa',             'Camisa'),
        ('saco',               'Saco'),
        ('smoking',            'Smoking completo'),
        ('dos_piezas',         'Traje 2 piezas'),
    # ── Infantil ─────────────────────────────
        ('infantil_general',   'General infantil'),
        ]

    # Información básica
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    tipo = models.CharField(max_length=50, choices=TIPOS)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Descripción
    descripcion_corta = models.TextField(max_length=300)
    descripcion_larga = models.TextField()
    
    # Especificaciones
    material = models.CharField(max_length=200, default="95% Poliéster, 5% Elastano")
    largo = models.CharField(max_length=100, blank=True)
    cuidado = models.CharField(max_length=200, default="Lavado a mano o seco")
    
    # Disponibilidad
    disponible = models.BooleanField(default=True)
    destacada = models.BooleanField(
        default=False,
        verbose_name="Prenda Destacada",
        help_text="Marcar si esta prenda debe aparecer en la página de inicio"
    )
    tallas_disponibles = models.CharField(
        max_length=50, 
        default="XS,S,M,L,XL",
        help_text="Separar con comas"
    )
    guia_tallas = models.JSONField(
        default=dict,
        blank=True,
        help_text="Guía de tallas específica para esta prenda"
    )
    colores_disponibles = models.CharField(
        max_length=200,
        default="",
        blank=True,
        help_text="Formato: Negro:#1a1a1a,Blanco:#ffffff"
    )
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Prenda"
        verbose_name_plural = "Prendas"
        ordering = ['-destacada', '-fecha_creacion']

    @property
    def imagen_principal(self):
        """
        Retorna el CloudinaryField de la imagen con orden=0.
        Retorna None si la prenda no tiene imágenes cargadas.
        Uso en templates: {{ prenda.imagen_principal.url }}
        """
        img = self.imagenes.filter(orden=0).first()
        return img.imagen if img else None

    @property
    def total_imagenes(self):
        """Cantidad de fotos cargadas para esta prenda (0–4)."""
        return self.imagenes.count()

    def get_tallas_list(self):
        return self.tallas_disponibles.split(',')
        
    def get_guia_tallas(self):
        from .guias_tallas import GUIAS_TALLAS, ENCABEZADOS_TALLAS
        guia = GUIAS_TALLAS.get(self.tipo, [])
        encabezados = ENCABEZADOS_TALLAS.get(self.tipo, ['Talla', 'Medidas'])
        return {
            'guia': guia,
            'encabezados': encabezados
        }
        
    def __str__(self):
        return self.nombre


class ImagenPrenda(models.Model):
    prenda = models.ForeignKey(Prenda, on_delete=models.CASCADE, related_name='imagenes')
    imagen = CloudinaryField(
        'imagen',
        help_text='Subí la foto de la prenda. Formatos aceptados: JPG, PNG, WEBP.',
    )
    orden = models.IntegerField(
        default=0,
        help_text='Posición en la galería. La imagen con orden 0 es la foto principal que aparece en el catálogo.',
    )

    class Meta:
        ordering = ['orden']
        verbose_name = 'Imagen'
        verbose_name_plural = 'Imágenes'

    @property
    def es_principal(self):
        return self.orden == 0

    def clean(self):
        if self.prenda_id:
            qs = ImagenPrenda.objects.filter(prenda_id=self.prenda_id)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.count() >= 4:
                raise ValidationError(
                    'No se pueden agregar más de 4 fotos por prenda. '
                    'Eliminá una foto existente antes de subir otra.'
                )

    def __str__(self):
        return f'{self.prenda.nombre} — imagen {self.orden}'