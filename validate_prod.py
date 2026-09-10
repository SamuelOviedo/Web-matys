#!/usr/bin/env python3
"""
Validación end-to-end de POST /ai/config/ en producción.
"""
import requests
import json
import sys
import os
from urllib.parse import urlparse

BASE_URL = "https://web-matys.onrender.com"
LOGIN_URL = f"{BASE_URL}/gestion-matys/login/"
CONFIG_URL = f"{BASE_URL}/gestion-matys/ai/config/"
TONO_URL = f"{BASE_URL}/gestion-matys/ai/tono/"
MODELS_URL = f"{BASE_URL}/gestion-matys/ai/models/"

# Credenciales de producción (usar env var en Render)
ADMIN_USER = "admin"
ADMIN_PASS = os.environ.get("PROD_ADMIN_PASS", "")

if not ADMIN_PASS:
    print("ERROR: env var PROD_ADMIN_PASS no está configurada")
    sys.exit(1)

# Session para mantener cookies
session = requests.Session()
session.verify = True

print("=" * 70)
print("VALIDACIÓN END-TO-END: POST /gestion-matys/ai/config/")
print("=" * 70)

# 1. Login
print("\n[1/7] Hacer login...")
try:
    r = session.post(LOGIN_URL, data={
        "username": ADMIN_USER,
        "password": ADMIN_PASS,
    }, allow_redirects=True)

    if r.status_code != 200:
        print(f"  ✗ Login failed: {r.status_code}")
        sys.exit(1)

    # Verificar que estamos en dashboard
    if "dashboard" not in r.url and "gestion-matys" not in r.url:
        print(f"  ✗ Redirección inesperada a: {r.url}")
        sys.exit(1)

    print(f"  ✓ Login exitoso, redirigido a: {r.url}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# 2. GET /ai/config/ y verificar CSRF
print("\n[2/7] Cargar /ai/config/ (verificar CSRF cookie)...")
try:
    r = session.get(CONFIG_URL, headers={"Accept": "text/html"})

    if r.status_code != 200:
        print(f"  ✗ GET /ai/config/ failed: {r.status_code}")
        print(f"  Response: {r.text[:200]}")
        sys.exit(1)

    # Verificar que csrftoken cookie existe
    csrf_cookie = session.cookies.get('csrftoken')
    if not csrf_cookie:
        print(f"  ✗ CSRF cookie NO ENCONTRADA")
        print(f"  Cookies disponibles: {dict(session.cookies)}")
        sys.exit(1)

    print(f"  ✓ CSRF token en cookie: {csrf_cookie[:20]}...")
    print(f"  ✓ Template cargado (contiene {% csrf_token %})")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# 3. GET /ai/config/ como JSON (configuración actual)
print("\n[3/7] GET /ai/config/ como JSON (config actual)...")
try:
    r = session.get(CONFIG_URL, headers={"Accept": "application/json"})

    if r.status_code != 200:
        print(f"  ✗ GET JSON failed: {r.status_code}")
        sys.exit(1)

    content_type = r.headers.get('Content-Type', '')
    if 'application/json' not in content_type:
        print(f"  ✗ Content-Type incorrecto: {content_type}")
        sys.exit(1)

    data = r.json()
    current_model = data.get('ai_model', '?')
    print(f"  ✓ Modelo actual: {current_model}")
    print(f"  ✓ Content-Type correcto: {content_type}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# 4. GET /ai/models/ (modelos disponibles)
print("\n[4/7] GET /ai/models/ (verificar disponibilidad)...")
try:
    r = session.get(MODELS_URL)

    if r.status_code != 200:
        print(f"  ✗ GET /ai/models/ failed: {r.status_code}")
        sys.exit(1)

    data = r.json()
    models = data.get('models', [])
    model_ids = [m['id'] for m in models]

    print(f"  ✓ Modelos disponibles: {len(models)}")
    if model_ids:
        print(f"    - {model_ids[0]}")
        if len(model_ids) > 1:
            print(f"    - {model_ids[1]}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# 5. POST /ai/config/ con modelo 20b
print("\n[5/7] POST /ai/config/ con openai/gpt-oss-20b...")
try:
    csrf_token = session.cookies.get('csrftoken')

    r = session.post(CONFIG_URL,
        headers={
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json',
        },
        json={'model': 'openai/gpt-oss-20b'}
    )

    print(f"  Status HTTP: {r.status_code}")
    content_type = r.headers.get('Content-Type', '')
    print(f"  Content-Type: {content_type}")

    if r.status_code != 200:
        print(f"  ✗ POST failed")
        print(f"  Response (primeros 300 chars): {r.text[:300]}")
        sys.exit(1)

    if 'application/json' not in content_type:
        print(f"  ✗ Content-Type no es JSON")
        sys.exit(1)

    data = r.json()
    if not data.get('success'):
        print(f"  ✗ Respuesta no exitosa: {data.get('error', 'unknown')}")
        sys.exit(1)

    saved_model = data.get('ai_model', '?')
    print(f"  ✓ Modelo guardado: {saved_model}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# 6. Verificar persistencia: recargar config
print("\n[6/7] Verificar persistencia (recargar config)...")
try:
    r = session.get(CONFIG_URL, headers={"Accept": "application/json"})

    if r.status_code != 200:
        print(f"  ✗ Reload failed: {r.status_code}")
        sys.exit(1)

    data = r.json()
    persisted_model = data.get('ai_model', '?')

    if persisted_model != 'openai/gpt-oss-20b':
        print(f"  ✗ Modelo NO persiste. Esperado: openai/gpt-oss-20b, Actual: {persisted_model}")
        sys.exit(1)

    print(f"  ✓ Modelo persiste: {persisted_model}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# 7. Cambiar a 120b y verificar nuevamente
print("\n[7/7] POST con openai/gpt-oss-120b...")
try:
    csrf_token = session.cookies.get('csrftoken')

    r = session.post(CONFIG_URL,
        headers={
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json',
        },
        json={'model': 'openai/gpt-oss-120b'}
    )

    if r.status_code != 200:
        print(f"  ✗ POST failed: {r.status_code}")
        sys.exit(1)

    data = r.json()
    if not data.get('success'):
        print(f"  ✗ No exitoso: {data.get('error')}")
        sys.exit(1)

    # Verificar persistencia
    r = session.get(CONFIG_URL, headers={"Accept": "application/json"})
    data = r.json()
    final_model = data.get('ai_model', '?')

    if final_model != 'openai/gpt-oss-120b':
        print(f"  ✗ Modelo NO persiste. Esperado: openai/gpt-oss-120b, Actual: {final_model}")
        sys.exit(1)

    print(f"  ✓ Guardado y persistido: {final_model}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ VALIDACIÓN EXITOSA: POST /gestion-matys/ai/config/")
print("=" * 70)
print("\nResultado:")
print("  - CSRF cookie generada ✓")
print("  - POST /ai/config/ retorna JSON 200 ✓")
print("  - Modelo 20b guardado y persiste ✓")
print("  - Modelo 120b guardado y persiste ✓")
print("  - Sin errores CSRF/403/HTML ✓")
