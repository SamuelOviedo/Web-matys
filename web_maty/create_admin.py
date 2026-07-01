import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_maty.settings')
django.setup()

from django.core.management import call_command
from django.core.management.base import CommandError


def ensure_superuser():
    from django.contrib.auth import get_user_model
    User = get_user_model()

    u = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    p = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    e = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

    if not p:
        print('No DJANGO_SUPERUSER_PASSWORD set, skipping.')
        return

    user, created = User.objects.get_or_create(username=u)
    user.set_password(p)
    user.email = e
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print('Superuser {} {}'.format(u, 'created' if created else 'updated'))


# Esperar a que la base de datos esté lista antes de tocarla. En el arranque
# del servicio (Render) Postgres puede tardar unos segundos en aceptar
# conexiones; sin esta espera, get_or_create lanzaría OperationalError y, al
# encadenarse con `&& gunicorn`, el servidor web nunca arrancaría y el
# despliegue quedaría marcado como fallido.
try:
    call_command('wait_for_db')
    ensure_superuser()
except CommandError as exc:
    # La creación del admin no es crítica para servir la aplicación: si la DB
    # no responde, registramos el aviso pero NO abortamos el arranque, para que
    # gunicorn igual levante. El superusuario se creará en el próximo arranque.
    print(f'Aviso: se omite la creación del admin ({exc}).')
except Exception as exc:  # pragma: no cover - defensa adicional en arranque
    print(f'Aviso: error inesperado creando el admin, se continúa: {exc}')
