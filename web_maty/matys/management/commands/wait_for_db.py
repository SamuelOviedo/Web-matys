"""Espera a que la base de datos acepte conexiones antes de continuar.

En despliegues (p. ej. Render) el servicio web y la base de datos gestionada
pueden arrancar casi a la vez: si Django ejecuta `migrate` o crea el superusuario
antes de que Postgres esté aceptando conexiones, se lanza `OperationalError` y el
arranque aborta, marcando el despliegue como fallido.

Este comando reintenta la conexión con una espera acotada, de modo que una
demora transitoria de la base de datos no rompa el despliegue. Si tras todos los
intentos sigue sin responder, falla de forma explícita (para que un problema
real de infraestructura se vea, no se oculte).

Uso:
    python manage.py wait_for_db            # valores por defecto
    python manage.py wait_for_db --attempts 30 --delay 2
"""
import os
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Espera a que la base de datos por defecto acepte conexiones.'

    def add_arguments(self, parser):
        parser.add_argument('--attempts', type=int,
                            default=int(os.environ.get('DB_WAIT_ATTEMPTS', 20)),
                            help='Número máximo de intentos (env DB_WAIT_ATTEMPTS, por defecto 20).')
        parser.add_argument('--delay', type=float,
                            default=float(os.environ.get('DB_WAIT_DELAY', 2.0)),
                            help='Segundos de espera entre intentos (env DB_WAIT_DELAY, por defecto 2).')

    def handle(self, *args, **options):
        attempts = options['attempts']
        delay = options['delay']
        conn = connections['default']

        for attempt in range(1, attempts + 1):
            try:
                conn.ensure_connection()
            except OperationalError as exc:
                self.stdout.write(
                    f'Base de datos no disponible (intento {attempt}/{attempts}): {exc}'
                )
                if attempt == attempts:
                    raise CommandError(
                        'La base de datos no respondió tras '
                        f'{attempts} intentos. Verificá DATABASE_URL y que la '
                        'instancia de Postgres esté activa.'
                    )
                time.sleep(delay)
            else:
                self.stdout.write(self.style.SUCCESS('Base de datos disponible.'))
                return
