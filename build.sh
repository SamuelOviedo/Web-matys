#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
cd web_maty
python manage.py collectstatic --no-input
python manage.py migrate
python - <<'PYEOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_maty.settings')
django.setup()
from django.contrib.auth.models import User
u = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
p = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
e = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
if p:
    user, created = User.objects.get_or_create(username=u)
    user.set_password(p)
    user.email = e
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print('Superuser {} {}'.format(u, 'created' if created else 'updated'))
PYEOF
