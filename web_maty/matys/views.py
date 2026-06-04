import json
import time
import cloudinary
import cloudinary.uploader
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Prenda, ImagenPrenda, TipoPrenda

_MAX_ATTEMPTS = 3
_COOLDOWN_SECONDS = 300  # 5 minutos

def inicio(request):
    prendas_destacadas = Prenda.objects.filter(destacada=True).prefetch_related('imagenes')[:3]
    context = {
        'title': "Inicio - Confecciones Maty's",
        'prendas_destacadas': prendas_destacadas,
    }
    return render(request, 'index.html', context)


def prendas(request):
    categoria = request.GET.get('categoria', '')
    tipo      = request.GET.get('tipo', '')

    qs = Prenda.objects.filter(disponible=True)
    if categoria:
        qs = qs.filter(categoria=categoria)
    if tipo:
        qs = qs.filter(tipo=tipo)

    paginator = Paginator(qs, 12)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    current = page_obj.number
    total   = paginator.num_pages
    nums    = sorted({1, total} | set(range(max(1, current - 2), min(total, current + 2) + 1)))
    page_range_display = []
    prev = None
    for n in nums:
        if prev and n - prev > 1:
            page_range_display.append('...')
        page_range_display.append(n)
        prev = n

    # Build menu dynamically from TipoPrenda so admin-panel changes sync instantly
    cat_map     = dict(Prenda.CATEGORIAS)
    tipo_map    = {t.slug: t.nombre for t in TipoPrenda.objects.filter(activo=True)}
    menu_render = []

    for cat_key, cat_label in Prenda.CATEGORIAS:
        tipos_activos = (
            TipoPrenda.objects
            .filter(categoria=cat_key, activo=True)
            .order_by('orden', 'nombre')
        )
        items = [(t.slug, t.nombre) for t in tipos_activos]
        grupos_render = [{'titulo': None, 'items': items}] if items else []
        menu_render.append({
            'key':            cat_key,
            'label':          cat_label,
            'grupos':         grupos_render,
            'tiene_subtipos': bool(items),
        })

    context = {
        'title':              "Prendas - Confecciones Maty's",
        'page_obj':           page_obj,
        'categoria_activa':   categoria,
        'tipo_activo':        tipo,
        'categoria_display':  cat_map.get(categoria, ''),
        'tipo_display':       tipo_map.get(tipo, tipo),
        'menu_render':        menu_render,
        'page_range_display': page_range_display,
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

    qs = Prenda.objects.all().order_by('-fecha_creacion')
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    tipo_map = dict(Prenda.TIPOS)
    for t in TipoPrenda.objects.filter(activo=True):
        tipo_map[t.slug] = t.nombre

    prendas_data = [(p, tipo_map.get(p.tipo, p.tipo)) for p in page_obj]

    current = page_obj.number
    total   = paginator.num_pages
    nums    = sorted({1, total} | set(range(max(1, current - 2), min(total, current + 2) + 1)))
    page_range = []
    prev = None
    for n in nums:
        if prev and n - prev > 1:
            page_range.append('...')
        page_range.append(n)
        prev = n

    context = {
        'active_nav':       'dashboard',
        'total_prendas':    Prenda.objects.count(),
        'total_disponibles':Prenda.objects.filter(disponible=True).count(),
        'total_imagenes':   ImagenPrenda.objects.count(),
        'sin_imagen':       Prenda.objects.filter(imagenes__isnull=True).count(),
        'prendas_data':     prendas_data,
        'page_obj':         page_obj,
        'page_range':       page_range,
    }
    return render(request, 'gestion_matys/dashboard.html', context)


def gestion_crear_prenda(request):
    if not _staff_required(request):
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)
    try:
        nombre            = request.POST.get('nombre', '').strip()
        precio            = request.POST.get('precio', '').strip()
        descripcion_corta = request.POST.get('descripcion_corta', '').strip()
        categoria         = request.POST.get('categoria', '').strip()
        tipo              = request.POST.get('tipo', '').strip()
        disponible        = request.POST.get('disponible') == 'true'
        por_encargo       = request.POST.get('por_encargo') == 'true'

        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre es requerido.'})
        if not precio:
            return JsonResponse({'success': False, 'error': 'El precio es requerido.'})
        if categoria not in [c[0] for c in Prenda.CATEGORIAS]:
            return JsonResponse({'success': False, 'error': 'Categoría inválida.'})

        base_slug = slugify(nombre)
        slug, counter = base_slug, 1
        while Prenda.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

        prenda = Prenda.objects.create(
            nombre=nombre,
            slug=slug,
            precio=precio,
            descripcion_corta=descripcion_corta,
            descripcion_larga=descripcion_corta or nombre,
            categoria=categoria,
            tipo=tipo,
            disponible=disponible,
            por_encargo=por_encargo,
        )

        for i in range(4):
            key = f'imagen_{i}'
            if key in request.FILES:
                result = cloudinary.uploader.upload(request.FILES[key])
                ImagenPrenda.objects.create(prenda=prenda, imagen=result['public_id'], orden=i)

        return JsonResponse({'success': True, 'prenda_id': prenda.pk})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def gestion_categorias(request):
    if not _staff_required(request):
        if request.method == 'POST':
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
        return redirect('gestion_login')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        try:
            if action == 'agregar':
                nombre = request.POST.get('nombre', '').strip()
                categoria = request.POST.get('categoria', '').strip()
                if not nombre:
                    return JsonResponse({'success': False, 'error': 'El nombre es requerido.'})
                if categoria not in ('femenino', 'masculino', 'infantil'):
                    return JsonResponse({'success': False, 'error': 'Categoría inválida.'})
                slug = slugify(nombre)
                if TipoPrenda.objects.filter(slug=slug, categoria=categoria).exists():
                    return JsonResponse({'success': False, 'error': 'Ya existe un tipo con ese nombre.'})
                TipoPrenda.objects.create(nombre=nombre, slug=slug, categoria=categoria)
                return JsonResponse({'success': True})

            if action == 'editar':
                tipo = get_object_or_404(TipoPrenda, pk=request.POST.get('id', ''))
                nombre = request.POST.get('nombre', '').strip()
                if not nombre:
                    return JsonResponse({'success': False, 'error': 'El nombre es requerido.'})
                tipo.nombre = nombre
                tipo.save()
                return JsonResponse({'success': True})

            if action == 'eliminar':
                tipo = get_object_or_404(TipoPrenda, pk=request.POST.get('id', ''))
                if Prenda.objects.filter(tipo=tipo.slug, categoria=tipo.categoria).exists():
                    return JsonResponse({'success': False, 'error': 'Hay prendas usando este tipo.'})
                tipo.delete()
                return JsonResponse({'success': True})

            return JsonResponse({'success': False, 'error': 'Acción inválida.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    context = {
        'active_nav': 'categorias',
        'tipos_femenino':  TipoPrenda.objects.filter(categoria='femenino').order_by('orden', 'nombre'),
        'tipos_masculino': TipoPrenda.objects.filter(categoria='masculino').order_by('orden', 'nombre'),
        'tipos_infantil':  TipoPrenda.objects.filter(categoria='infantil').order_by('orden', 'nombre'),
    }
    return render(request, 'gestion_matys/categorias.html', context)


def gestion_tipos_json(request):
    if not _staff_required(request):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    categoria = request.GET.get('categoria', '')
    qs = TipoPrenda.objects.filter(activo=True)
    if categoria:
        qs = qs.filter(categoria=categoria)
    return JsonResponse({'tipos': list(qs.values('id', 'nombre', 'slug', 'categoria'))})


def gestion_imagenes(request):
    if not _staff_required(request):
        return redirect('gestion_login')
    from django.db.models import Prefetch
    prendas_qs = (
        Prenda.objects
        .prefetch_related(
            Prefetch(
                'imagenes',
                queryset=ImagenPrenda.objects.order_by('orden'),
                to_attr='imagenes_ordenadas',
            )
        )
        .filter(imagenes__isnull=False)
        .distinct()
        .order_by('nombre')
    )
    prendas = []
    for prenda in prendas_qs:
        principal = prenda.imagenes_ordenadas[0] if prenda.imagenes_ordenadas else None
        url = ''
        if principal:
            try:
                url = cloudinary.CloudinaryImage(str(principal.imagen)).build_url(secure=True)
            except Exception:
                url = ''
        prendas.append({
            'prenda': prenda,
            'url': url,
            'total_fotos': len(prenda.imagenes_ordenadas),
        })
    context = {
        'active_nav': 'imagenes',
        'prendas': prendas,
        'total_imagenes': len(prendas),
    }
    return render(request, 'gestion_matys/imagenes.html', context)


def gestion_editar_prenda(request, prenda_id):
    if not _staff_required(request):
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)

    prenda = get_object_or_404(Prenda, pk=prenda_id)

    if request.method == 'GET':
        imagenes_data = []
        for img in prenda.imagenes.order_by('orden'):
            try:
                url = cloudinary.CloudinaryImage(str(img.imagen)).build_url(secure=True)
            except Exception:
                url = ''
            imagenes_data.append({'id': img.pk, 'url': url, 'orden': img.orden})
        return JsonResponse({
            'id': prenda.pk,
            'nombre': prenda.nombre,
            'precio': str(prenda.precio),
            'descripcion_corta': prenda.descripcion_corta,
            'categoria': prenda.categoria,
            'tipo': prenda.tipo,
            'disponible': prenda.disponible,
            'por_encargo': prenda.por_encargo,
            'imagenes': imagenes_data,
        })

    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            precio = request.POST.get('precio', '').strip()
            descripcion_corta = request.POST.get('descripcion_corta', '').strip()
            categoria = request.POST.get('categoria', '').strip()
            tipo = request.POST.get('tipo', '').strip()
            disponible = request.POST.get('disponible') == 'true'
            por_encargo = request.POST.get('por_encargo') == 'true'

            if not nombre:
                return JsonResponse({'success': False, 'error': 'El nombre es requerido.'})
            if not precio:
                return JsonResponse({'success': False, 'error': 'El precio es requerido.'})

            valid_categorias = [c[0] for c in Prenda.CATEGORIAS]
            if categoria not in valid_categorias:
                return JsonResponse({'success': False, 'error': 'Categoría inválida.'})
            static_tipos = {t[0] for t in Prenda.TIPOS}
            tipo_valid = (
                not tipo or
                TipoPrenda.objects.filter(slug=tipo, categoria=categoria).exists() or
                tipo in static_tipos
            )
            if not tipo_valid:
                return JsonResponse({'success': False, 'error': 'Tipo inválido.'})

            prenda.nombre = nombre
            prenda.precio = precio
            prenda.descripcion_corta = descripcion_corta
            prenda.categoria = categoria
            prenda.tipo = tipo
            prenda.disponible = disponible
            prenda.por_encargo = por_encargo
            prenda.save()

            # Delete images (only while at least 1 remains)
            eliminar_raw = request.POST.get('eliminar_imagen_ids', '')
            if eliminar_raw:
                try:
                    ids_to_delete = json.loads(eliminar_raw)
                    if isinstance(ids_to_delete, list):
                        remaining = prenda.imagenes.count()
                        for img_id in ids_to_delete:
                            if remaining > 1:
                                ImagenPrenda.objects.filter(pk=img_id, prenda=prenda).delete()
                                remaining -= 1
                except (json.JSONDecodeError, TypeError):
                    pass

            # Reorder images
            orden_raw = request.POST.get('orden_imagenes', '')
            if orden_raw:
                try:
                    for item in json.loads(orden_raw):
                        ImagenPrenda.objects.filter(pk=item['id'], prenda=prenda).update(orden=item['orden'])
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass

            # Upload new image
            if 'imagen_nueva' in request.FILES:
                max_orden = (
                    prenda.imagenes.order_by('-orden')
                    .values_list('orden', flat=True)
                    .first()
                )
                next_orden = (max_orden + 1) if max_orden is not None else 0
                result = cloudinary.uploader.upload(request.FILES['imagen_nueva'])
                ImagenPrenda.objects.create(
                    prenda=prenda,
                    imagen=result['public_id'],
                    orden=next_orden,
                )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


def gestion_eliminar_prenda(request, prenda_id):
    if not _staff_required(request):
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

    prenda = get_object_or_404(Prenda, pk=prenda_id)
    try:
        for img in prenda.imagenes.all():
            try:
                cloudinary.uploader.destroy(str(img.imagen))
            except Exception:
                pass
        prenda.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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