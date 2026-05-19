import time
import cloudinary
import cloudinary.uploader
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
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
    imagenes_qs = ImagenPrenda.objects.select_related('prenda').order_by('prenda__nombre', 'orden')
    # Precompute URLs using build_url (same pattern as admin.py) to avoid
    # CloudinaryField.url silently failing when config isn't resolved at template render.
    imagenes = []
    for img in imagenes_qs:
        try:
            url = cloudinary.CloudinaryImage(str(img.imagen)).build_url(secure=True)
        except Exception:
            url = ''
        imagenes.append({'img': img, 'url': url})
    context = {
        'active_nav': 'imagenes',
        'imagenes': imagenes,
        'total_imagenes': len(imagenes),
    }
    return render(request, 'gestion_matys/imagenes.html', context)


def gestion_editar_prenda(request, prenda_id):
    if not _staff_required(request):
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)

    prenda = get_object_or_404(Prenda, pk=prenda_id)

    if request.method == 'GET':
        img_principal = prenda.imagenes.filter(orden=0).first()
        img_url = ''
        if img_principal:
            try:
                img_url = cloudinary.CloudinaryImage(str(img_principal.imagen)).build_url(secure=True)
            except Exception:
                img_url = ''
        return JsonResponse({
            'id': prenda.pk,
            'nombre': prenda.nombre,
            'precio': str(prenda.precio),
            'descripcion_corta': prenda.descripcion_corta,
            'categoria': prenda.categoria,
            'tipo': prenda.tipo,
            'disponible': prenda.disponible,
            'imagen_url': img_url,
        })

    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            precio = request.POST.get('precio', '').strip()
            descripcion_corta = request.POST.get('descripcion_corta', '').strip()
            categoria = request.POST.get('categoria', '').strip()
            tipo = request.POST.get('tipo', '').strip()
            disponible = request.POST.get('disponible') == 'true'

            if not nombre:
                return JsonResponse({'success': False, 'error': 'El nombre es requerido.'})
            if not precio:
                return JsonResponse({'success': False, 'error': 'El precio es requerido.'})

            valid_categorias = [c[0] for c in Prenda.CATEGORIAS]
            valid_tipos = [t[0] for t in Prenda.TIPOS]
            if categoria not in valid_categorias:
                return JsonResponse({'success': False, 'error': 'Categoría inválida.'})
            if tipo not in valid_tipos:
                return JsonResponse({'success': False, 'error': 'Tipo inválido.'})

            prenda.nombre = nombre
            prenda.precio = precio
            prenda.descripcion_corta = descripcion_corta
            prenda.categoria = categoria
            prenda.tipo = tipo
            prenda.disponible = disponible
            prenda.save()

            if 'imagen' in request.FILES:
                result = cloudinary.uploader.upload(request.FILES['imagen'])
                img_obj, _ = ImagenPrenda.objects.get_or_create(prenda=prenda, orden=0)
                img_obj.imagen = result['public_id']
                img_obj.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


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