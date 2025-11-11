from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def inicio(request):
    context = {
        'title': 'Inicio - Confecciones Maty\'s',
    }
    return render(request, 'index.html', context)

def prendas(request):
    context = {
        'title': 'Prendas - Confecciones Maty\'s',
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

def detalle_prendas(request):
    context = {
        'title': 'Detalle de Prenda - Confecciones Maty\'s',
    }
    return render(request, 'detalle_prendas.html', context)