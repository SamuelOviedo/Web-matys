from django.db import migrations, models

NEW_TIPOS = [
    # Femenino — vestidos detail
    ('Vestido de gala',        'vestido_gala',       'femenino', 10),
    ('Vestido casual',         'vestido_casual',     'femenino', 11),
    ('Vestido semiformal',     'vestido_semiformal', 'femenino', 12),
    ('Vestido de novia',       'vestido_novia',      'femenino', 13),
    ('Vestido de quinceañera', 'vestido_quince',     'femenino', 14),
    ('Vestido alusivo',        'vestido_alusivo',    'femenino', 15),
    ('Vestido playero',        'vestido_playero',    'femenino', 16),
    ('Traje alusivo',          'traje_alusivo',      'femenino', 17),
    # Masculino — extras
    ('Smoking completo',       'smoking',            'masculino', 10),
    ('Traje 2 piezas',         'dos_piezas',         'masculino', 11),
    # Infantil
    ('General infantil',       'infantil_general',   'infantil', 0),
]


def populate(apps, schema_editor):
    TipoPrenda = apps.get_model('matys', 'TipoPrenda')
    for nombre, slug, categoria, orden in NEW_TIPOS:
        TipoPrenda.objects.get_or_create(
            slug=slug,
            categoria=categoria,
            defaults={'nombre': nombre, 'orden': orden, 'activo': True},
        )


def depopulate(apps, schema_editor):
    TipoPrenda = apps.get_model('matys', 'TipoPrenda')
    for _, slug, categoria, _ in NEW_TIPOS:
        TipoPrenda.objects.filter(slug=slug, categoria=categoria).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('matys', '0006_alter_prenda_categoria_tipo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipoprenda',
            name='categoria',
            field=models.CharField(
                choices=[
                    ('femenino',  'Femenino'),
                    ('masculino', 'Masculino'),
                    ('infantil',  'Infantil'),
                ],
                max_length=20,
            ),
        ),
        migrations.RunPython(populate, depopulate),
    ]
