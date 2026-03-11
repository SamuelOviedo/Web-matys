from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Prenda 

def inicio(request):
    prendas_destacadas = Prenda.objects.filter(destacada=True)[:3]
    context = {
        'title': 'Inicio - Confecciones Maty\'s',
        'prendas_destacadas': prendas_destacadas,
    }
    return render(request, 'index.html', context)

def prendas(request):
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
        'whatsapp_number': '50498267040',
        'facebook_url': 'https://www.facebook.com/maryurihern/reels/',
        'instagram_url': 'https://www.instagram.com/confe_ccionesmaty?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==',
        'tiktok_url': 'https://www.tiktok.com/@confeccinesmaty4?is_from_webapp=1&sender_device=pc',
        'youtube_url': 'https://youtube.com/@maty-2020?si=ncsHDzw-QCMJGlX1',
    }
    return render(request, 'contacto.html', context)

def detalle_prendas(request, slug):
    prenda = get_object_or_404(Prenda, slug=slug, disponible=True)
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