import json
import os
import logging
import cloudinary
import cloudinary.uploader
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.core.paginator import Paginator
from django.db import models
from .models import Prenda, ImagenPrenda, TipoPrenda, SiteConfig, AIUsage
from .site_textos import SECCIONES_TEXTOS, DEFAULTS_TEXTOS, VALIDACIONES_TEXTOS, get_textos

logger = logging.getLogger(__name__)


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
    q         = request.GET.get('q', '').strip()

    cat_map = dict(Prenda.CATEGORIAS)
    # Etiqueta visible de cada tipo: TipoPrenda (dinámico) + TIPOS (estático).
    tipo_map = dict(Prenda.TIPOS)
    for t in TipoPrenda.objects.filter(activo=True):
        tipo_map[t.slug] = t.nombre

    # ── Catálogo base: solo prendas disponibles ───────────────────────
    qs = Prenda.objects.filter(disponible=True)
    if categoria:
        qs = qs.filter(categoria=categoria)
    if tipo:
        qs = qs.filter(tipo=tipo)

    # ── Búsqueda de texto: nombre, descripciones, categoría y tipo ────
    if q:
        from django.db.models import Q
        ql = q.lower()
        # Categorías cuyo nombre visible coincide con la búsqueda.
        cat_keys = [k for k, label in Prenda.CATEGORIAS if ql in label.lower()]
        # Tipos cuyo nombre visible coincide con la búsqueda.
        tipo_keys = [slug for slug, label in tipo_map.items() if ql in label.lower()]
        filtro = (
            Q(nombre__icontains=q)
            | Q(descripcion_corta__icontains=q)
            | Q(descripcion_larga__icontains=q)
        )
        if cat_keys:
            filtro |= Q(categoria__in=cat_keys)
        if tipo_keys:
            filtro |= Q(tipo__in=tipo_keys)
        qs = qs.filter(filtro)

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

    # Contexto compartido entre la página completa y el fragmento AJAX.
    resultados_context = {
        'page_obj':           page_obj,
        'categoria_activa':   categoria,
        'tipo_activo':        tipo,
        'busqueda':           q,
        'categoria_display':  cat_map.get(categoria, ''),
        'tipo_display':       tipo_map.get(tipo, tipo),
        'page_range_display': page_range_display,
    }

    # Petición AJAX (filtro sin recargar): devolver SOLO el fragmento de
    # resultados. El front-end reemplaza el contenedor del catálogo y
    # sincroniza la URL con la History API.
    is_partial = (
        request.GET.get('partial') == '1'
        or request.headers.get('x-requested-with') == 'XMLHttpRequest'
    )
    if is_partial:
        return render(request, 'prendas/_resultados.html', resultados_context)

    # ── Menú dinámico: ocultar categorías/tipos SIN prendas disponibles ─
    # (solo para la página completa; el fragmento AJAX no lo necesita)
    # Conjuntos calculados solo desde prendas disponibles, para que una
    # categoría o tipo vacío nunca aparezca en la navegación.
    disponibles      = Prenda.objects.filter(disponible=True)
    cats_con_prendas = set(disponibles.values_list('categoria', flat=True))
    pares_con_prendas = set(disponibles.values_list('categoria', 'tipo'))

    menu_render = []
    for cat_key, cat_label in Prenda.CATEGORIAS:
        if cat_key not in cats_con_prendas:
            continue  # categoría sin prendas → no se muestra
        tipos_activos = (
            TipoPrenda.objects
            .filter(categoria=cat_key, activo=True)
            .order_by('orden', 'nombre')
        )
        # Solo tipos que tengan al menos una prenda disponible en esta categoría.
        items = [
            (t.slug, t.nombre)
            for t in tipos_activos
            if (cat_key, t.slug) in pares_con_prendas
        ]
        grupos_render = [{'titulo': None, 'items': items}] if items else []
        menu_render.append({
            'key':            cat_key,
            'label':          cat_label,
            'grupos':         grupos_render,
            'tiene_subtipos': bool(items),
        })

    context = {
        'title':       "Prendas - Confecciones Maty's",
        'menu_render': menu_render,
        **resultados_context,
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


def gestion_ayuda(request):
    """Centro de ayuda: tutoriales guiados interactivos del panel.

    La página es un contenedor; el listado de tutoriales se construye en el
    cliente desde el registro único (static/js/admin_tours.js), de modo que
    agregar un tutorial no requiere tocar el backend.
    """
    if not _staff_required(request):
        return redirect('gestion_login')
    return render(request, 'gestion_matys/ayuda.html', {'active_nav': 'ayuda'})


def gestion_logout(request):
    logout(request)
    return redirect('inicio')


def gestion_ai_tono(request):
    if not _staff_required(request):
        logger.warning(f"[ai_tono POST] no autorizado: user={request.user.username}, staff={request.user.is_staff}")
        return JsonResponse({'error': 'No autorizado'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    from groq import Groq
    from .models import AIUsage

    try:
        logger.info(f"[ai_tono POST] inicio: user={request.user.username}")

        data = json.loads(request.body)
        descripcion = data.get('descripcion', '').strip()
        if not descripcion:
            logger.warning(f"[ai_tono POST] descripción vacía")
            return JsonResponse({'error': 'Descripción vacía'}, status=400)

        # Obtener modelo de configuración o usar fallback
        config = SiteConfig.get_solo()
        model_name = config.data.get('ai_model', 'openai/gpt-oss-20b')
        logger.info(f"[ai_tono POST] modelo={model_name}, desc_len={len(descripcion)}")

        logger.info(f"[ai_tono POST] llamando Groq...")
        client = Groq(api_key=os.environ.get('GROQ_API_KEY', ''))
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Eres un asistente de copywriting para Confecciones Matys, una tienda de ropa. '
                        'Respondes siempre con JSON válido y nada más.'
                    ),
                },
                {
                    'role': 'user',
                    'content': (
                        f'Reescribe esta descripción de prenda en 4 tonos distintos (máx 20 palabras cada uno):\n'
                        f'"{descripcion}"\n\n'
                        'Responde SOLO con este JSON exacto, sin texto adicional:\n'
                        '{"tonos":[{"nombre":"Profesional","texto":"..."},{"nombre":"Casual","texto":"..."},{"nombre":"Emocional","texto":"..."},{"nombre":"Juvenil","texto":"..."}]}'
                    ),
                },
            ],
            temperature=0.75,
            max_tokens=400,
        )

        # Capturar respuesta y consumo
        usage = completion.usage
        raw = completion.choices[0].message.content.strip()
        logger.info(f"[ai_tono POST] Groq OK: status=200, tokens={{prompt:{usage.prompt_tokens},completion:{usage.completion_tokens},total:{usage.total_tokens}}}")

        # Intentar parsear JSON de forma robusta
        try:
            # Paso 1: Intentar parse directo
            result = None
            parse_error = None

            try:
                result = json.loads(raw.strip())
                logger.info(f"[ai_tono POST] JSON parse directo OK")
            except json.JSONDecodeError as e:
                logger.warning(f"[ai_tono POST] JSON parse directo falló, intentando alternativas...")
                parse_error = e
                # Paso 2: Si falló, intentar extraer JSON de markdown code blocks
                # Formato esperado: ```json\n{...}\n```
                if '```' in raw:
                    # Buscar contenido entre triple backticks
                    parts = raw.split('```')
                    for part in parts:
                        if part.strip().startswith('{'):
                            # Encontramos potencial JSON
                            try:
                                result = json.loads(part.strip())
                                parse_error = None
                                break
                            except json.JSONDecodeError:
                                continue

            # Si aún no tenemos resultado, intentar buscar bloque JSON por { y }
            if result is None and parse_error is not None:
                # Buscar primer { y último }
                start_idx = raw.find('{')
                end_idx = raw.rfind('}')
                if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                    potential_json = raw[start_idx:end_idx + 1]
                    try:
                        result = json.loads(potential_json)
                        parse_error = None
                    except json.JSONDecodeError:
                        pass

            # Si todavía no tenemos un resultado, fallar con el error original
            if result is None:
                logger.error(f"[ai_tono POST] JSON parse falló completamente")
                raise parse_error if parse_error else json.JSONDecodeError('No JSON found', raw, 0)

            # Registrar como exitosa solo si JSON es válido
            logger.info(f"[ai_tono POST] éxito: modelo={model_name} registrando AIUsage")
            AIUsage.objects.create(
                model=model_name,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                status='success'
            )
            return JsonResponse(result)

        except json.JSONDecodeError as je:
            # JSON parsing falló pero Groq respondió
            # Registrar como error con tokens consumidos
            logger.warning(f"[ai_tono POST] JSON parse error: {type(je).__name__}, registrando error AIUsage")
            AIUsage.objects.create(
                model=model_name,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                status='error',
                error_message=f'JSON parse error: {str(je)[:200]}'
            )
            # Retornar error amigable sin detalles técnicos
            return JsonResponse({
                'error': 'El modelo seleccionado no generó una respuesta válida. Intenta con otro modelo o edita manualmente los tonos.'
            }, status=500)

    except Exception as e:
        # Error antes de o durante llamada a Groq
        # Registrar error sin tokens (Groq no respondió)
        try:
            config = SiteConfig.get_solo()
            model_name_error = config.data.get('ai_model', 'openai/gpt-oss-20b')
            AIUsage.objects.create(
                model=model_name_error,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                status='error',
                error_message=str(e)[:500]
            )
        except:
            pass

        # Retornar error amigable
        error_msg = 'Error al conectar con el servicio de IA. Intenta más tarde.'
        if 'api_key' in str(e).lower():
            error_msg = 'Configuración de IA no disponible.'
        elif 'timeout' in str(e).lower():
            error_msg = 'Timeout: el servicio de IA tardó demasiado. Intenta de nuevo.'

        return JsonResponse({'error': error_msg}, status=500)


def _get_ai_consumption_today():
    """
    Helper: calcula consumo IA del día actual.
    Suma tokens de TODAS las llamadas que tengan total_tokens > 0 (success y error con respuesta).
    Diferencia entre llamadas exitosas y fallidas.
    Reutilizado por gestion_ai_usage y gestion_ai_config.
    """
    from django.utils import timezone

    today = timezone.now().date()
    today_start = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.min.time())
    )
    today_end = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.max.time())
    )

    # Todas las llamadas del día
    all_calls = AIUsage.objects.filter(
        timestamp__gte=today_start,
        timestamp__lte=today_end
    ).aggregate(
        # Tokens consumidos: suma REAL de tokens (todas las llamadas)
        total_tokens=models.Sum('total_tokens', default=0),
        # Llamadas totales
        total_calls=models.Count('id'),
        # Llamadas exitosas
        success_calls=models.Count('id', filter=models.Q(status='success')),
        # Llamadas fallidas
        error_calls=models.Count('id', filter=models.Q(status='error')),
    )

    total_tokens = all_calls.get('total_tokens', 0) or 0
    total_calls = all_calls.get('total_calls', 0) or 0
    success_calls = all_calls.get('success_calls', 0) or 0
    error_calls = all_calls.get('error_calls', 0) or 0

    daily_limit = int(os.environ.get('AI_DAILY_TOKEN_LIMIT', '10000'))
    percentage = int((total_tokens / daily_limit) * 100) if daily_limit > 0 else 0
    percentage = min(percentage, 100)

    return {
        'tokens_used': total_tokens,
        'daily_limit': daily_limit,
        'percentage': percentage,
        'calls_today': total_calls,
        'success_calls': success_calls,
        'error_calls': error_calls,
        'remaining': max(0, daily_limit - total_tokens),
    }


def gestion_ai_usage(request):
    """
    Endpoint que devuelve el consumo actual de IA (tokens hoy + % de límite).
    Reutiliza datos existentes de AIUsage sin duplicar cálculos.
    """
    if not _staff_required(request):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    consumption = _get_ai_consumption_today()
    return JsonResponse(consumption)


def gestion_ai_models(request):
    """
    Endpoint que retorna lista de modelos disponibles en Groq API.
    Filtra solo modelos compatibles con chat/completions (gestion_ai_tono).
    Usa allowlist de familias conocidas + exclusión explícita de incompatibles.
    IMPORTANTE: Retorna INTERSECCIÓN de modelos reales de Groq + allowlist.
    Nunca devuelve un modelo solo porque coincide con allowlist si Groq no lo tiene.
    """
    if not _staff_required(request):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    try:
        import requests
        groq_api_key = os.environ.get('GROQ_API_KEY', '')
        if not groq_api_key:
            return JsonResponse({'models': [], 'error': 'GROQ_API_KEY no configurada'})

        # Consultar Groq API para listar modelos ACTUALMENTE DISPONIBLES
        headers = {'Authorization': f'Bearer {groq_api_key}'}
        response = requests.get('https://api.groq.com/openai/v1/models', headers=headers, timeout=5)

        if response.status_code != 200:
            return JsonResponse({'models': [], 'error': 'Error al conectar con Groq'})

        data = response.json()
        all_models = data.get('data', [])

        # Obtener lista de IDs ACTUALMENTE DISPONIBLES
        available_model_ids = {m['id'] for m in all_models}

        # Allowlist: familias de modelos conocidas y compatibles con chat
        # Estos son validados manualmente como compatibles con /chat/completions
        # Nota: Groq usa namespaces (ej: openai/gpt-oss-20b, meta-llama/...)
        compatible_prefixes = [
            'mixtral-',                  # Mistral (si existe sin namespace)
            'llama-3',                   # Llama 3 (si existe sin namespace)
            'gemma-',                    # Gemma (si existe sin namespace)
            'openai/gpt-oss-',           # OpenAI OSS (con namespace openai/)
            'meta-llama/llama-3',        # Meta Llama 3 (con namespace meta-llama/)
            'allam-',                    # Allam (Arabic LLM)
            'qwen/qwen',                 # Qwen (con namespace qwen/)
        ]

        # Exclusiones explícitas: modelos no compatibles con chat/completions
        excluded_keywords = [
            'whisper',       # Transcripción de audio
            'guard',         # Moderación / safety guards
            'prompt-guard',  # Groq safety guard
            'moderation',    # Moderación
            'tts',           # Text-to-speech
            'audio',         # Audio
            'embed',         # Embeddings
            'embedding',     # Embeddings
            'orpheus',       # Non-chat models (canopylabs)
            'safeguard',     # Safety/moderation models
        ]

        def is_compatible(model_id):
            model_lower = model_id.lower()

            # Excluir explícitamente incompatibles
            if any(kw in model_lower for kw in excluded_keywords):
                return False

            # Incluir si match con allowlist
            if any(model_lower.startswith(prefix) for prefix in compatible_prefixes):
                return True

            # Fallback conservador: excluir si no está en allowlist
            return False

        # INTERSECCIÓN: solo modelos que están en Groq Y en allowlist
        chat_models = [
            {'id': m['id'], 'name': m.get('id', '')}
            for m in all_models
            if is_compatible(m['id']) and m['id'] in available_model_ids
        ]

        return JsonResponse({'models': chat_models})

    except Exception as e:
        return JsonResponse({'models': [], 'error': f'Error: {str(e)[:100]}'})


def gestion_ai_config(request):
    """
    Vista/API para configuración de modelo IA.
    GET (browser): renderiza template
    GET (fetch): retorna JSON con modelo + consumo
    POST (fetch): guarda nuevo modelo
    """
    if not _staff_required(request):
        # Si es GET browser, redirige a login
        if request.method == 'GET' and 'application/json' not in request.headers.get('Accept', ''):
            return redirect('gestion_login')
        return JsonResponse({'error': 'No autorizado'}, status=403)

    # GET browser request → render template
    if request.method == 'GET' and 'application/json' not in request.headers.get('Accept', ''):
        return render(request, 'gestion_matys/ai_config.html', {
            'active_nav': 'ia_config'
        })

    if request.method == 'GET':
        # Retornar configuración actual + consumo + validación modelo
        config = SiteConfig.get_solo()
        ai_model = config.data.get('ai_model', 'openai/gpt-oss-20b')
        model_is_valid = True
        model_warning = None

        # Verificar si el modelo actual está disponible en Groq
        try:
            import requests
            groq_api_key = os.environ.get('GROQ_API_KEY', '')
            if groq_api_key:
                headers = {'Authorization': f'Bearer {groq_api_key}'}
                response = requests.get('https://api.groq.com/openai/v1/models', headers=headers, timeout=5)
                if response.status_code == 200:
                    data_models = response.json()
                    model_ids = [m['id'] for m in data_models.get('data', [])]
                    if ai_model not in model_ids:
                        model_is_valid = False
                        model_warning = f'Modelo "{ai_model}" ya no está disponible en Groq. Selecciona otro desde la lista.'
        except Exception as e:
            # Si no podemos conectar a Groq, asumimos que el modelo es válido
            pass

        # Obtener consumo del día (usar helper reutilizado)
        consumption = _get_ai_consumption_today()

        response_data = {
            'ai_model': ai_model,
            'model_is_valid': model_is_valid,
            'tokens_used': consumption['tokens_used'],
            'daily_limit': consumption['daily_limit'],
            'percentage': consumption['percentage'],
            'calls_today': consumption['calls_today'],
            'remaining': consumption['remaining'],
        }

        if model_warning:
            response_data['model_warning'] = model_warning

        return JsonResponse(response_data)

    elif request.method == 'POST':
        try:
            logger.info(f"[ai_config POST] user={request.user.username}, staff={request.user.is_staff}")

            data = json.loads(request.body)
            new_model = data.get('model', '').strip()
            logger.info(f"[ai_config POST] parsed model={new_model}")

            if not new_model:
                logger.warning(f"[ai_config POST] modelo no especificado")
                return JsonResponse({'error': 'Modelo no especificado'}, status=400)

            # Validar que el modelo existe en Groq
            import requests
            groq_api_key = os.environ.get('GROQ_API_KEY', '')
            if not groq_api_key:
                logger.error(f"[ai_config POST] GROQ_API_KEY no configurada")
                return JsonResponse({'error': 'GROQ_API_KEY no configurada'}, status=500)

            logger.info(f"[ai_config POST] validando modelo {new_model} en Groq...")
            headers = {'Authorization': f'Bearer {groq_api_key}'}
            response = requests.get('https://api.groq.com/openai/v1/models', headers=headers, timeout=5)

            if response.status_code != 200:
                logger.error(f"[ai_config POST] Groq models list failed: status={response.status_code}")
                return JsonResponse({'error': 'Error al validar modelo en Groq'}, status=500)

            data_models = response.json()
            model_ids = [m['id'] for m in data_models.get('data', [])]
            logger.info(f"[ai_config POST] Groq models: {len(model_ids)} disponibles")

            if new_model not in model_ids:
                logger.warning(f"[ai_config POST] modelo {new_model} no en lista Groq")
                return JsonResponse({'error': f'Modelo {new_model} no encontrado en Groq'}, status=400)

            # Guardar en SiteConfig
            logger.info(f"[ai_config POST] guardando {new_model} en SiteConfig...")
            config = SiteConfig.get_solo()
            config.data['ai_model'] = new_model
            config.save()

            logger.info(f"[ai_config POST] éxito: modelo={new_model} guardado")
            return JsonResponse({'success': True, 'ai_model': new_model})

        except json.JSONDecodeError as e:
            logger.exception(f"[ai_config POST] JSON decode error")
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.exception(f"[ai_config POST] excepción: {type(e).__name__}")
            return JsonResponse({'error': f'Error: {str(e)[:100]}'}, status=500)

    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)


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