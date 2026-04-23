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
if p and not User.objects.filter(username=u).exists():
    User.objects.create_superuser(u, e, p)
    print(f'Superuser {u} created')
else:
    print(f'Superuser {u} already exists or no password set')
PYEOF
