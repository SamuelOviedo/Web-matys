#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
cd web_maty
python manage.py collectstatic --no-input
python manage.py migrate
python create_admin.py
