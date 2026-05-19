from django.db import migrations


TIPOS_DATA = [
    # (nombre, slug, categoria, orden)
    ('Vestido',  'vestido',  'femenino', 0),
    ('Blusa',    'blusa',    'femenino', 1),
    ('Falda',    'falda',    'femenino', 2),
    ('Chaleco',  'chaleco',  'femenino', 3),
    ('Pantalón', 'pantalon', 'femenino', 4),
    ('Saco',     'saco',     'femenino', 5),
    ('Suéter',   'sueter',   'femenino', 6),
    ('Traje',    'traje',    'femenino', 7),
    ('Camisa',   'camisa',   'masculino', 0),
    ('Pantalón', 'pantalon', 'masculino', 1),
    ('Chaleco',  'chaleco',  'masculino', 2),
    ('Saco',     'saco',     'masculino', 3),
    ('Traje',    'traje',    'masculino', 4),
]


def populate_tipos(apps, schema_editor):
    TipoPrenda = apps.get_model('matys', 'TipoPrenda')
    for nombre, slug, categoria, orden in TIPOS_DATA:
        TipoPrenda.objects.get_or_create(
            slug=slug,
            categoria=categoria,
            defaults={'nombre': nombre, 'orden': orden, 'activo': True},
        )


def depopulate_tipos(apps, schema_editor):
    TipoPrenda = apps.get_model('matys', 'TipoPrenda')
    slugs = {(slug, cat) for _, slug, cat, _ in TIPOS_DATA}
    for slug, cat in slugs:
        TipoPrenda.objects.filter(slug=slug, categoria=cat).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('matys', '0004_alter_imagenprenda_imagen_alter_imagenprenda_orden_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_tipos, depopulate_tipos),
    ]
