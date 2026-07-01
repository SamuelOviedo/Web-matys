#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
cd web_maty
python manage.py collectstatic --no-input
# Esperar a que Postgres acepte conexiones evita que `migrate` falle con
# OperationalError si la base de datos aún se está iniciando.
python manage.py wait_for_db
python manage.py migrate
