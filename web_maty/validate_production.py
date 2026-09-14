#!/usr/bin/env python3
"""
Validación REAL de endpoints IA en producción (https://web-matys.onrender.com)
No requiere acceso local. Simula cliente real con cookies/CSRF.
"""
import requests
import json
from datetime import datetime

BASE_URL = "https://web-matys.onrender.com"
ADMIN_USER = "admin"  # Usuario producción (si existe)
ADMIN_PASS = "admin"  # Contraseña de test

print("=" * 70)
print("VALIDACIÓN PRODUCCIÓN: Panel Matys IA Config")
print("=" * 70)
print(f"\nBase URL: {BASE_URL}")
print(f"Timestamp: {datetime.now().isoformat()}\n")

session = requests.Session()

# ========== 1. Login
print("[TEST 1] POST /gestion-matys/login/")
try:
    # Primero GET login page para obtener CSRF
    login_page = session.get(f"{BASE_URL}/gestion-matys/login/")
    print(f"  GET login page: {login_page.status_code}")

    # Parse CSRF token desde HTML
    import re
    csrf_match = re.search(r'csrfmiddlewaretoken["\']?\s*value=["\']([^"\']+)', login_page.text)
    csrf_token = csrf_match.group(1) if csrf_match else None

    if not csrf_token:
        print("  ⚠ No CSRF token found, attempting without...")
        csrf_token = ""

    # POST login
    login_data = {
        'username': ADMIN_USER,
        'password': ADMIN_PASS,
        'csrfmiddlewaretoken': csrf_token,
    }
    login_resp = session.post(f"{BASE_URL}/gestion-matys/login/", data=login_data, allow_redirects=False)
    print(f"  POST login: {login_resp.status_code}")

    if login_resp.status_code in (302, 200):
        print("  ✓ Login attempt successful")
    else:
        print(f"  ⚠ Login returned {login_resp.status_code} (may be auth error or redirect issue)")

except Exception as e:
    print(f"  ERROR: {e}")

# ========== 2. GET /gestion-matys/ai/config/?format=json
print("\n[TEST 2] GET /gestion-matys/ai/config/?format=json")
try:
    resp = session.get(f"{BASE_URL}/gestion-matys/ai/config/?format=json")
    content_type = resp.headers.get('Content-Type', '')
    print(f"  Status: {resp.status_code}")
    print(f"  Content-Type: {content_type}")

    if resp.status_code == 200:
        if 'application/json' in content_type:
            try:
                data = resp.json()
                print(f"  ✓ JSON válido - keys: {list(data.keys())}")
                print(f"    ai_model: {data.get('ai_model')}")
                print(f"    tokens_used: {data.get('tokens_used')}")
                print(f"    percentage: {data.get('percentage')}%")
            except json.JSONDecodeError:
                print(f"  ERROR: No JSON válido. Body (primeros 300 chars):\n{resp.text[:300]}")
        else:
            print(f"  ERROR: Content-Type no es JSON, es {content_type}")
            print(f"  Body (primeros 300 chars):\n{resp.text[:300]}")
    else:
        print(f"  ERROR: Status {resp.status_code}, no 200")
        if 'text/html' in content_type:
            print(f"  Body es HTML (el problema original):\n{resp.text[:300]}")
except Exception as e:
    print(f"  ERROR: {e}")

# ========== 3. GET /gestion-matys/ai/models/
print("\n[TEST 3] GET /gestion-matys/ai/models/")
try:
    resp = session.get(f"{BASE_URL}/gestion-matys/ai/models/")
    content_type = resp.headers.get('Content-Type', '')
    print(f"  Status: {resp.status_code}")
    print(f"  Content-Type: {content_type}")

    if resp.status_code == 200 and 'application/json' in content_type:
        data = resp.json()
        models = data.get('models', [])
        print(f"  Total modelos: {len(models)}")

        compound_models = [m for m in models if 'compound' in m.get('id', '').lower()]
        if compound_models:
            print(f"  ✓ groq/compound encontrados: {len(compound_models)}")
            for m in compound_models:
                print(f"    - {m['id']}")
        else:
            print(f"  ⚠ No groq/compound encontrados")

        if len(models) > 0:
            print(f"  Primeros 3 modelos:")
            for m in models[:3]:
                print(f"    - {m['id']}")
    else:
        print(f"  ERROR: No JSON o status != 200")
except Exception as e:
    print(f"  ERROR: {e}")

# ========== 4. GET /gestion-matys/ai/config/ (sin ?format=json - debe retornar HTML)
print("\n[TEST 4] GET /gestion-matys/ai/config/ (sin ?format=json)")
try:
    resp = session.get(f"{BASE_URL}/gestion-matys/ai/config/")
    content_type = resp.headers.get('Content-Type', '')
    print(f"  Status: {resp.status_code}")
    print(f"  Content-Type: {content_type}")

    if 'text/html' in content_type:
        print(f"  ✓ Retorna HTML correctamente")
    else:
        print(f"  ⚠ Content-Type no es text/html: {content_type}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 70)
print("VALIDACIÓN COMPLETADA")
print("=" * 70)
