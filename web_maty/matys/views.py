from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Prenda 

# Create your views here.
def inicio(request):
    context = {
        'title': 'Inicio - Confecciones Maty\'s',
    }
    return render(request, 'index.html', context)

def prendas(request):
        # Obtener todas las prendas de la base de datos
    productos = Prenda.objects.filter(disponible=True)
    context = {
        'title': 'Prendas - Confecciones Maty\'s',
        'productos': productos,
    }
    return render(request, 'prendas.html', context)

def trayectoria(request):
    context = {
        'title': 'Nuestra Trayectoria - Confecciones Maty\'s',
    }
    return render(request, 'trayectoria.html', context)

def contacto(request):
    context = {
        'title': 'Contáctanos - Confecciones Maty\'s',
        'contacts': [
            {'name_store': 'Atención al Cliente', 'advicer': 'María Torres'},
            {'name_store': 'Ventas', 'advicer': 'Carlos Gómez'},
        ]
    }
    return render(request, 'contacto.html', context)

def detalle_prendas(request, slug):
    # Obtener la prenda específica por su slug
    prenda = get_object_or_404(Prenda, slug=slug, disponible=True)
    
    # Obtener productos relacionados (misma categoría)
    relacionados = Prenda.objects.filter(
        categoria=prenda.categoria,
        disponible=True
    ).exclude(id=prenda.id)[:4]
    
    context = {
        'title': f'{prenda.nombre} - Detalle',
        'prenda': prenda,
        'relacionados': relacionados,
    }
    return render(request, 'detalle_prendas.html', context)