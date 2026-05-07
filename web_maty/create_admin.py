import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_maty.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

u = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
p = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
e = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

if not p:
    print('No DJANGO_SUPERUSER_PASSWORD set, skipping.')
else:
    user, created = User.objects.get_or_create(username=u)
    user.set_password(p)
    user.email = e
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print('Superuser {} {}'.format(u, 'created' if created else 'updated'))
