from django.db import models

# Create your models here.

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
    slug = models.SlugField(unique=True)  # Para la URL amigable
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
    tallas_disponibles = models.CharField(
        max_length=50, 
        default="XS,S,M,L,XL",
        help_text="Separar con comas"
    )
    colores_disponibles = models.CharField(
        max_length=200,
        default="Negro,Blanco",
        help_text="Formato: Negro:#1a1a1a,Blanco:#ffffff"
    )
    
    # Imágenes
    imagen_principal = models.CharField(max_length=500)  # URL de la imagen
    imagen_2 = models.CharField(max_length=500, blank=True)
    imagen_3 = models.CharField(max_length=500, blank=True)
    imagen_4 = models.CharField(max_length=500, blank=True)
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Prenda"
        verbose_name_plural = "Prendas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return self.nombre
    
    def get_tallas_list(self):
        """Devuelve lista de tallas"""
        return self.tallas_disponibles.split(',')
    
    def get_colores_dict(self):
        """Devuelve diccionario de colores {nombre: hex}"""
        colores = {}
        if self.colores_disponibles:
            for item in self.colores_disponibles.split(','):
                if ':' in item:
                    nombre, hex_color = item.split(':')
                    colores[nombre.strip()] = hex_color.strip()
        return colores