from django.db import models

class Prenda(models.Model):
    CATEGORIAS = [
        ('femenino', 'Femenino'),
        ('masculino', 'Masculino'),
    ]
    
    TIPOS = [
        ('vestido', 'Vestido'),
        ('blusa', 'Blusa'),
        ('falda', 'Falda'),
        ('chaleco', 'Chaleco'),
        ('pantalon', 'Pantalón'),
        ('camisa', 'Camisa'),
        ('saco', 'Saco'),
        ('sueter', 'Suéter'),
        ('traje', 'Traje'),
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
    
    # Imágenes
    imagen_principal = models.ImageField(max_length=500)
    imagen_2 = models.ImageField(max_length=500, blank=True)
    imagen_3 = models.ImageField(max_length=500, blank=True)
    imagen_4 = models.ImageField(max_length=500, blank=True)
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Prenda"
        verbose_name_plural = "Prendas"
        ordering = ['-destacada', '-fecha_creacion']

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