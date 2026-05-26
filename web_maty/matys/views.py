import time
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Prenda

# ── Estructura del menú ────────────────────────────────────────
MENU_ESTRUCTURA = [
    {
        'key':   'femenino',
        'label': 'Femenino',
        'grupos': [
            {
                'titulo': 'Vestidos',
                'tipos':  [
                    'vestido_gala', 'vestido_casual', 'vestido_semiformal',
                    'vestido_novia', 'vestido_quince', 'vestido_alusivo', 'vestido_playero',
                ],
            },
            {
                'titulo': None,
                'tipos':  ['blusa', 'falda', 'chaleco', 'pantalon', 'traje', 'traje_alusivo'],
            },
        ],
    },
    {
        'key':   'masculino',
        'label': 'Masculino',
        'grupos': [
            {
                'titulo': None,
                'tipos':  ['pantalon', 'sueter', 'camisa', 'saco'],
            },
            {
                'titulo': 'Traje',
                'tipos':  ['smoking', 'dos_piezas'],
            },
        ],
    },
    {
        'key':    'infantil',
        'label':  'Infantil',
        'grupos': [],
    },
]

# ── Vistas ─────────────────────────────────────────────────────

def inicio(request):
    prendas_destacadas = Prenda.objects.filter(destacada=True)[:3]
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
    nums    = sorted({1, total} | set(range(max(1, current-2), min(total, current+2)+1)))
    page_range_display = []
    prev = None
    for n in nums:
        if prev and n - prev > 1:
            page_range_display.append('...')
        page_range_display.append(n)
        prev = n

    tipo_map    = dict(Prenda.TIPOS)
    menu_render = []

    for cat in MENU_ESTRUCTURA:
        cat_key = cat['key']
        tipos_en_bd = set(
            Prenda.objects
            .filter(disponible=True, categoria=cat_key)
            .values_list('tipo', flat=True)
            .distinct()
        )
        grupos_render = []
        for grupo in cat['grupos']:
            items = [
                (t, tipo_map.get(t, t))
                for t in grupo['tipos']
                if t in tipos_en_bd
            ]
            if items:
                grupos_render.append({
                    'titulo': grupo['titulo'],
                    'items':  items,
                })
        menu_render.append({
            'key':            cat_key,
            'label':          cat['label'],
            'grupos':         grupos_render,
            'tiene_subtipos': bool(grupos_render),
        })

    cat_map = dict(Prenda.CATEGORIAS)

    context = {
        'title':              "Prendas - Confecciones Maty's",
        'page_obj':           page_obj,
        'categoria_activa':   categoria,
        'tipo_activo':        tipo,
        'categoria_display':  cat_map.get(categoria, ''),
        'tipo_display':       tipo_map.get(tipo, ''),
        'menu_render':        menu_render,
        'page_range_display': page_range_display,
    }
    return render(request, 'prendas.html', context)


def trayectoria(request):
    context = {
        'title': "Nuestra Trayectoria - Confecciones Maty's",
    }
    return render(request, 'trayectoria.html', context)


def contacto(request):
    context = {
        'title':           "Contáctanos - Confecciones Maty's",
        'whatsapp_number': '50498267040',
        'facebook_url':    'https://www.facebook.com/maryurihern/reels/',
        'instagram_url':   'https://www.instagram.com/confe_ccionesmaty?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==',
        'tiktok_url':      'https://www.tiktok.com/@confeccinesmaty4?is_from_webapp=1&sender_device=pc',
        'youtube_url':     'https://youtube.com/@maty-2020?si=ncsHDzw-QCMJGlX1',
    }
    return render(request, 'contacto.html', context)


def detalle_prendas(request, slug):
    prenda = get_object_or_404(Prenda, slug=slug, disponible=True)
    relacionados = Prenda.objects.filter(
        categoria=prenda.categoria,
        disponible=True
    ).exclude(id=prenda.id)[:4]

    context = {
        'title':       f'{prenda.nombre} - Detalle',
        'prenda':      prenda,
        'relacionados': relacionados,
    }
    return render(request, 'detalle_prendas.html', context)


def admin_login(request):
    if request.user.is_authenticated:
        return redirect('/admin/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('/admin/')
        else:
            messages.error(request, 'Credenciales incorrectas o sin permisos de acceso.')

    return render(request, 'acceso.html', {
        'title': 'Acceso Administrativo',
    })