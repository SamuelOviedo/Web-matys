from django.db import migrations, models
import django.db.models.deletion
import cloudinary.models


class Migration(migrations.Migration):

    dependencies = [
        ('matys', '0002_add_destacada_column'),
    ]

    operations = [
        migrations.RemoveField(model_name='prenda', name='imagen_principal'),
        migrations.RemoveField(model_name='prenda', name='imagen_2'),
        migrations.RemoveField(model_name='prenda', name='imagen_3'),
        migrations.RemoveField(model_name='prenda', name='imagen_4'),
        migrations.CreateModel(
            name='ImagenPrenda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', cloudinary.models.CloudinaryField(max_length=255, verbose_name='imagen')),
                ('orden', models.IntegerField(default=0)),
                ('prenda', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='imagenes',
                    to='matys.prenda',
                )),
            ],
            options={
                'verbose_name': 'Imagen',
                'verbose_name_plural': 'Imágenes',
                'ordering': ['orden'],
            },
        ),
    ]
