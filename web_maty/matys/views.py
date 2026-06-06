import json
import cloudinary
import cloudinary.uploader
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.core.paginator import Paginator
from .models import Prenda, ImagenPrenda, TipoPrenda, SiteConfig
from .site_textos import SECCIONES_TEXTOS, DEFAULTS_TEXTOS, VALIDACIONES_TEXTOS, get_textos


def inicio(request):
    # Solo prendas destacadas Y disponibles: una prenda oculta no debe
    # aparecer en la portada (su detalle daría 404).
    prendas_destacadas = (
        Prenda.objects
        .filter(destacada=True, disponible=True)
        .prefetch_related('imagenes')[:3]
    )
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

def admin_login(request):
    # Ruta heredada (/acceso/): el modal de login al que redirigía ya no
    # existe. Se mantiene la URL y se envía al login real del panel.
    return redirect('gestion_login')


def trayectoria(request):
    context = {
        'title': 'Nuestra Trayectoria - Confecciones Maty\'s',
    }
    return render(request, 'trayectoria.html', context)

def contacto(request):
    txt = get_textos()
    context = {
        'title': 'Contáctanos - Confecciones Maty\'s',
        'whatsapp_number': txt['contacto_whatsapp'],
        'facebook_url': txt['red_facebook'],
        'instagram_url': txt['red_instagram'],
        'tiktok_url': txt['red_tiktok'],
        'youtube_url': txt['red_youtube'],
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
        destacada         = request.POST.get('destacada') == 'true'

        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre es requerido.'})
        if not precio:
            return JsonResponse({'success': False, 'error': 'El precio es requerido.'})
        if categoria not in [c[0] for c in Prenda.CATEGORIAS]:
            return JsonResponse({'success': False, 'error': 'Categoría inválida.'})
        static_tipos = {t[0] for t in Prenda.TIPOS}
        tipo_valid = (
            not tipo or
            TipoPrenda.objects.filter(slug=tipo, categoria=categoria).exists() or
            tipo in static_tipos
        )
        if not tipo_valid:
            return JsonResponse({'success': False, 'error': 'Tipo inválido.'})

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
            destacada=destacada,
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
            'destacada': prenda.destacada,
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
            # Solo actualizar si el formulario los envía: el modal de
            # "Imágenes" no incluye estos campos y antes los reseteaba.
            if 'por_encargo' in request.POST:
                prenda.por_encargo = request.POST.get('por_encargo') == 'true'
            if 'destacada' in request.POST:
                prenda.destacada = request.POST.get('destacada') == 'true'
            prenda.save()

            nueva_subida = 'imagen_nueva' in request.FILES

            # 1) Eliminar imágenes: valida que quede al menos una foto
            #    (contando la nueva, si la hay) y destruye en Cloudinary.
            eliminar_raw = request.POST.get('eliminar_imagen_ids', '')
            if eliminar_raw:
                try:
                    ids_to_delete = json.loads(eliminar_raw)
                except (json.JSONDecodeError, TypeError):
                    ids_to_delete = []
                if isinstance(ids_to_delete, list) and ids_to_delete:
                    qs_del = prenda.imagenes.filter(pk__in=ids_to_delete)
                    final_count = (
                        prenda.imagenes.count() - qs_del.count()
                        + (1 if nueva_subida else 0)
                    )
                    if final_count < 1:
                        return JsonResponse({
                            'success': False,
                            'error': 'La prenda debe conservar al menos una imagen.',
                        })
                    for img in qs_del:
                        try:
                            cloudinary.uploader.destroy(str(img.imagen))
                        except Exception:
                            pass  # si Cloudinary falla, igual quitamos la referencia
                        img.delete()

            # 2) Reordenar imágenes según el orden visual del panel
            orden_raw = request.POST.get('orden_imagenes', '')
            if orden_raw:
                try:
                    for item in json.loads(orden_raw):
                        ImagenPrenda.objects.filter(
                            pk=item['id'], prenda=prenda
                        ).update(orden=item['orden'])
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass

            # 3) Subir imagen nueva (máx. 4 por prenda, también en servidor)
            if nueva_subida:
                if prenda.imagenes.count() >= 4:
                    return JsonResponse({
                        'success': False,
                        'error': 'Máximo 4 imágenes por prenda. Eliminá una antes de subir otra.',
                    })
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

            # 4) Re-compactar la secuencia: garantiza que siempre exista
            #    orden=0 (la imagen principal del catálogo) sin huecos.
            for i, img in enumerate(prenda.imagenes.order_by('orden', 'pk')):
                if img.orden != i:
                    img.orden = i
                    img.save(update_fields=['orden'])

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
    """Editor de textos del sitio público (CMS ligero sobre SiteConfig)."""
    if not _staff_required(request):
        if request.method == 'POST':
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
        return redirect('gestion_login')

    if request.method == 'POST':
        try:
            # Validar antes de guardar
            url_validator = URLValidator(schemes=['http', 'https'])
            for key, regla in VALIDACIONES_TEXTOS.items():
                val = request.POST.get(key, '').strip()
                if not val:
                    continue  # vacío = vuelve al default, siempre válido
                if regla == 'digits' and not val.isdigit():
                    return JsonResponse({
                        'success': False,
                        'error': 'El número de WhatsApp debe contener solo dígitos '
                                 '(ej: 50498267040).',
                    })
                if regla == 'url':
                    try:
                        url_validator(val)
                    except ValidationError:
                        return JsonResponse({
                            'success': False,
                            'error': f'"{val[:60]}" no es una URL válida. '
                                     'Debe comenzar con https://',
                        })

            cfg = SiteConfig.get_solo()
            data = dict(cfg.data or {})
            for key, default in DEFAULTS_TEXTOS.items():
                if key not in request.POST:
                    continue
                val = request.POST.get(key, '').strip()
                if val and val != default:
                    data[key] = val
                else:
                    # vacío o igual al original → quitar override (vuelve al default)
                    data.pop(key, None)
            cfg.data = data
            cfg.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    textos = get_textos()
    overrides = set()
    try:
        overrides = {
            k for k, v in (SiteConfig.get_solo().data or {}).items()
            if k in DEFAULTS_TEXTOS and isinstance(v, str) and v.strip()
        }
    except Exception:
        pass

    secciones = []
    for seccion in SECCIONES_TEXTOS:
        campos = []
        for campo in seccion['campos']:
            campos.append({
                **campo,
                'valor': textos[campo['key']],
                'modificado': campo['key'] in overrides,
            })
        secciones.append({**seccion, 'campos': campos})

    return render(request, 'gestion_matys/inicio.html', {
        'active_nav': 'inicio_admin',
        'secciones': secciones,
    })


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