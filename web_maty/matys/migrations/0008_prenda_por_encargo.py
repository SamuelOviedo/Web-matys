from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matys', '0007_tipoproenda_infantil_and_new_tipos'),
    ]

    operations = [
        migrations.AddField(
            model_name='prenda',
            name='por_encargo',
            field=models.BooleanField(
                default=True,
                help_text="Muestra el ribbon 'Por encargo' en la tarjeta del catálogo público.",
                verbose_name='Hecho por encargo',
            ),
        ),
    ]
