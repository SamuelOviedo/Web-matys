import time
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Prenda, ImagenPrenda

_MAX_ATTEMPTS = 3
_COOLDOWN_SECONDS = 300  # 5 minutos

def inicio(request):
    prendas_destacadas = Prenda.objects.filter(destacada=True).prefetch_related('imagenes')[:3]
    context = {
        'title': 'Inicio - Confecciones Maty\'s',
        'prendas_destacadas': prendas_destacadas,
    }
    return render(request, 'index.html', context)

def prendas(request):
    productos = Prenda.objects.filter(disponible=True).prefetch_related('imagenes')
    context = {
        'title': 'Prendas - Confecciones Maty\'s',
        'productos': productos,
        'show_admin_modal': request.GET.get('modal') == '1',
    }
    return render(request, 'prendas.html', context)

@require_POST
def admin_login(request):
    now = time.time()
    attempts = request.session.get('_login_attempts', 0)
    last_attempt_time = request.session.get('_login_last_attempt', 0.0)

    # Resetear contador si ya pasó el cooldown
    if (now - last_attempt_time) >= _COOLDOWN_SECONDS:
        attempts = 0
        request.session['_login_attempts'] = 0

    # Bloqueo temporal
    if attempts >= _MAX_ATTEMPTS and (now - last_attempt_time) < _COOLDOWN_SECONDS:
        remaining = int(_COOLDOWN_SECONDS - (now - last_attempt_time))
        messages.error(
            request,
            f'Demasiados intentos fallidos. Intenta nuevamente en {remaining // 60 + 1} minuto(s).',
            extra_tags='blocked',
        )
        return redirect('/prendas/?modal=1')

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()

    # Validación: vacíos y longitud mínima
    if not username or not password or len(username) < 3 or len(password) < 3:
        attempts += 1
        request.session['_login_attempts'] = attempts
        request.session['_login_last_attempt'] = now
        messages.error(request, 'Credenciales incorrectas.')
        return redirect('/prendas/?modal=1')

    user = authenticate(request, username=username, password=password)

    if user is not None and (user.is_staff or user.is_superuser):
        request.session.pop('_login_attempts', None)
        request.session.pop('_login_last_attempt', None)
        login(request, user)  # Django cicla el session key internamente
        return redirect('/admin/')

    attempts += 1
    request.session['_login_attempts'] = attempts
    request.session['_login_last_attempt'] = now
    messages.error(request, 'Credenciales incorrectas.')
    return redirect('/prendas/?modal=1')

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

def gestion_login(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('gestion_dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('gestion_dashboard')
        error = 'Credenciales incorrectas.'

    return render(request, 'gestion_matys/login.html', {'error': error})


def _staff_required(request):
    return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)


def gestion_dashboard(request):
    if not _staff_required(request):
        return redirect('gestion_login')
    context = {
        'active_nav': 'dashboard',
        'total_prendas': Prenda.objects.count(),
        'total_disponibles': Prenda.objects.filter(disponible=True).count(),
        'total_imagenes': ImagenPrenda.objects.count(),
        'sin_imagen': Prenda.objects.filter(imagenes__isnull=True).count(),
        'prendas': Prenda.objects.prefetch_related('imagenes').order_by('-fecha_creacion')[:20],
    }
    return render(request, 'gestion_matys/dashboard.html', context)


def gestion_categorias(request):
    if not _staff_required(request):
        return redirect('gestion_login')
    context = {
        'active_nav': 'categorias',
        'tipos_femenino': ['Vestido', 'Blusa', 'Falda', 'Chaleco', 'Pantalón', 'Saco', 'Suéter', 'Traje'],
        'tipos_masculino': ['Camisa', 'Pantalón', 'Chaleco', 'Saco', 'Traje'],
    }
    return render(request, 'gestion_matys/categorias.html', context)


def gestion_imagenes(request):
    if not _staff_required(request):
        return redirect('gestion_login')
    imagenes = ImagenPrenda.objects.select_related('prenda').order_by('prenda__nombre', 'orden')
    context = {
        'active_nav': 'imagenes',
        'imagenes': imagenes,
        'total_imagenes': imagenes.count(),
    }
    return render(request, 'gestion_matys/imagenes.html', context)


def gestion_inicio(request):
    if not _staff_required(request):
        return redirect('gestion_login')
    return render(request, 'gestion_matys/inicio.html', {'active_nav': 'inicio_admin'})


def gestion_logout(request):
    logout(request)
    return redirect('inicio')


def detalle_prendas(request, slug):
    prenda = get_object_or_404(Prenda.objects.prefetch_related('imagenes'), slug=slug, disponible=True)
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