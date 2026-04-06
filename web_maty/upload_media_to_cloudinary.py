"""
Script de migración: agrupa imágenes de media/ por prefijo, las sube a Cloudinary
y crea registros Prenda con URLs válidas de producción.
Uso: python upload_media_to_cloudinary.py
"""
import os
import sys
import django
import urllib.request
from pathlib import Path

# ─── Setup ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_maty.settings')
django.setup()  # carga .env automáticamente vía settings.py

import cloudinary
import cloudinary.uploader
from django.conf import settings
from django.utils.text import slugify
from matys.models import Prenda

# ─── Verificar configuración Cloudinary ──────────────────────────────────────
cfg = settings.CLOUDINARY_STORAGE
assert cfg.get('CLOUD_NAME'), "ERROR: CLOUDINARY_CLOUD_NAME no está definido."
assert cfg.get('API_KEY'),    "ERROR: CLOUDINARY_API_KEY no está definido."
assert cfg.get('API_SECRET'), "ERROR: CLOUDINARY_API_SECRET no está definido."

cloudinary.config(
    cloud_name=cfg['CLOUD_NAME'],
    api_key=cfg['API_KEY'],
    api_secret=cfg['API_SECRET'],
)
print(f"Cloudinary configurado: cloud_name={cfg['CLOUD_NAME']}\n")

# ─── Constantes ──────────────────────────────────────────────────────────────
MEDIA_DIR    = BASE_DIR / 'media'
VALID_EXTS   = {'.jpg', '.jpeg', '.png', '.webp'}
SKIP_PREFIXES = ('contactA', 'V7', 'WhatsApp')

# ─── Datos de cada prenda (edita nombre/precio/etc. según corresponda) ────────
PRENDA_DATA = {
    'prenda1': {
        'nombre':            'Prenda 1',
        'categoria':         'femenino',
        'tipo':              'vestido',
        'precio':            '350.00',
        'descripcion_corta': 'Hermosa prenda confeccionada a mano con materiales de calidad.',
        'descripcion_larga': 'Hermosa prenda confeccionada a mano con materiales de alta calidad. Disponible en varios colores y tallas.',
        'material':          '95% Poliéster, 5% Elastano',
        'cuidado':           'Lavado a mano o seco',
        'tallas_disponibles': 'XS,S,M,L,XL',
        'disponible':        True,
        'destacada':         True,
    },
    'prenda2': {
        'nombre':            'Prenda 2',
        'categoria':         'femenino',
        'tipo':              'blusa',
        'precio':            '250.00',
        'descripcion_corta': 'Elegante prenda con acabados impecables y diseño exclusivo.',
        'descripcion_larga': 'Elegante prenda con acabados impecables y diseño exclusivo. Confeccionada con dedicación.',
        'material':          '100% Algodón',
        'cuidado':           'Lavado a mano',
        'tallas_disponibles': 'XS,S,M,L,XL',
        'disponible':        True,
        'destacada':         True,
    },
    'prenda3': {
        'nombre':            'Prenda 3',
        'categoria':         'femenino',
        'tipo':              'falda',
        'precio':            '200.00',
        'descripcion_corta': 'Prenda versátil y cómoda, ideal para el día a día.',
        'descripcion_larga': 'Prenda versátil y cómoda, ideal para el día a día con comodidad y elegancia.',
        'material':          '95% Poliéster, 5% Elastano',
        'cuidado':           'Lavado a mano o seco',
        'tallas_disponibles': 'XS,S,M,L,XL',
        'disponible':        True,
        'destacada':         True,
    },
}

# ─── Helpers ─────────────────────────────────────────────────────────────────
def es_principal(f):
    """True si el archivo es la imagen base: prendaX.EXT sin sufijo aleatorio."""
    return '_' not in f.stem

def upload(filepath, field_name):
    """
    Sube a Cloudinary con public_id='media/<field_name>' (sin extensión).
    django-cloudinary-storage prepende 'media/' al valor guardado en DB,
    por lo que guardamos solo <field_name> y subimos a media/<field_name>.
    """
    public_id = f'media/{field_name}'
    try:
        cloudinary.uploader.upload(
            str(filepath),
            public_id=public_id,
            overwrite=True,
        )
        return field_name  # valor a guardar en ImageField
    except Exception as e:
        print(f'  [ERROR subiendo {filepath.name}]: {e}')
        return None

def verificar_url(url):
    try:
        code = urllib.request.urlopen(url, timeout=6).getcode()
        return code == 200
    except Exception:
        return False

# ─── Agrupar archivos por prefijo ────────────────────────────────────────────
grupos = {}
for f in sorted(MEDIA_DIR.iterdir()):
    if not f.is_file():
        continue
    if f.suffix.lower() not in VALID_EXTS:
        continue
    if any(f.name.startswith(s) for s in SKIP_PREFIXES):
        continue
    prefix = f.stem.split('_')[0]
    grupos.setdefault(prefix, []).append(f)

print(f'Grupos detectados: {list(grupos.keys())}\n')

# ─── Limpiar DB ──────────────────────────────────────────────────────────────
eliminados = Prenda.objects.all().delete()
print(f'DB limpia. Registros eliminados: {eliminados[0]}\n')

# ─── Subir y crear registros ─────────────────────────────────────────────────
errores = []

for group_name, archivos in grupos.items():
    if group_name not in PRENDA_DATA:
        print(f'[SKIP] {group_name} — sin datos en PRENDA_DATA\n')
        continue

    data = PRENDA_DATA[group_name]
    print(f'[{group_name}] {len(archivos)} archivos encontrados')

    principal_file = next((f for f in archivos if es_principal(f)), archivos[0])
    adicionales    = [f for f in archivos if f != principal_file][:3]

    print(f'  principal  : {principal_file.name}')
    field_principal = upload(principal_file, group_name)
    if not field_principal:
        errores.append(group_name)
        continue

    fields_extra = []
    for i, img in enumerate(adicionales, start=2):
        print(f'  imagen_{i}   : {img.name}')
        val = upload(img, f'{group_name}_img{i}')
        if val:
            fields_extra.append(val)

    prenda = Prenda.objects.create(
        slug             = slugify(data['nombre']),
        nombre           = data['nombre'],
        categoria        = data['categoria'],
        tipo             = data['tipo'],
        precio           = data['precio'],
        descripcion_corta= data['descripcion_corta'],
        descripcion_larga= data['descripcion_larga'],
        material         = data['material'],
        cuidado          = data['cuidado'],
        tallas_disponibles=data['tallas_disponibles'],
        disponible       = data['disponible'],
        destacada        = data['destacada'],
        imagen_principal = field_principal,
        imagen_2         = fields_extra[0] if len(fields_extra) > 0 else '',
        imagen_3         = fields_extra[1] if len(fields_extra) > 1 else '',
        imagen_4         = fields_extra[2] if len(fields_extra) > 2 else '',
    )

    # Verificar URLs
    for campo in ['imagen_principal', 'imagen_2', 'imagen_3', 'imagen_4']:
        img_field = getattr(prenda, campo)
        if not img_field:
            continue
        url = img_field.url
        ok  = verificar_url(url)
        estado = 'OK  ' if ok else 'FAIL'
        print(f'  [{estado}] {url}')
        if not ok:
            errores.append(url)

    print()

# ─── Resumen ─────────────────────────────────────────────────────────────────
print('=' * 55)
print(f'Total prendas en DB : {Prenda.objects.count()}')
if errores:
    print(f'Errores             : {len(errores)}')
    for e in errores:
        print(f'  - {e}')
else:
    print('Todas las URLs verificadas correctamente.')
print('Migracion completada.')
