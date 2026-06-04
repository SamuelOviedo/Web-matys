from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matys', '0005_tipoproenda_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prenda',
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
        migrations.AlterField(
            model_name='prenda',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('vestido_gala',       'Vestido de gala'),
                    ('vestido_casual',     'Vestido casual'),
                    ('vestido_semiformal', 'Vestido semiformal'),
                    ('vestido_novia',      'Vestido de novia'),
                    ('vestido_quince',     'Vestido de quinceañera'),
                    ('vestido_alusivo',    'Vestido alusivo'),
                    ('vestido_playero',    'Vestido playero'),
                    ('blusa',              'Blusa'),
                    ('falda',              'Falda'),
                    ('chaleco',            'Chaleco'),
                    ('pantalon',           'Pantalón'),
                    ('traje',              'Traje'),
                    ('traje_alusivo',      'Traje alusivo'),
                    ('sueter',             'Suéter'),
                    ('camisa',             'Camisa'),
                    ('saco',               'Saco'),
                    ('smoking',            'Smoking completo'),
                    ('dos_piezas',         'Traje 2 piezas'),
                    ('infantil_general',   'General infantil'),
                ],
                max_length=50,
            ),
        ),
    ]
