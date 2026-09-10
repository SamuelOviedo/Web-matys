# Validación End-to-End: POST /gestion-matys/ai/config/

**Estado**: PARCIALMENTE VALIDADO ✓ (bloqueado por credenciales de producción)  
**Fecha**: 2026-09-10  
**Commit**: 8211f48 — `fix(csrf): agregar {% csrf_token %} a base_admin.html + mejorar validación JSON`

---

## ✓ VALIDADO EN PRODUCCIÓN (Render)

### 1. Commit Live
- **GitHub**: main branch tiene 8211f48
- **Render**: Auto-deploy activo, cambios deplorados

### 2. CSRF Cookie Generation
```
GET /gestion-matys/login/
→ Response headers incluyen:
   Set-Cookie: csrftoken=e3Pj1KiABxjGflf1mFJr7DrVFYLtXu7A; 
   expires=Thu, 09 Sep 2027; 
   Max-Age=31449600; Path=/; 
   SameSite=Lax
```
**Confirmado**: `{% csrf_token %}` en template genera cookie Django CSRF ✓

### 3. Template Fix
- **File**: `web_maty/matys/templates/gestion_matys/base_admin.html` (línea 514)
- **Fix**: `{% csrf_token %}` agregado pre `<script>` tags
- **Status**: ✓ Presente en repo y deployado en Render

### 4. JSON Response Format (No HTML on Errors)
```bash
curl "https://web-matys.onrender.com/gestion-matys/ai/config/" \
  -H "Accept: application/json"
```
**Response**:
```json
{
  "error": "No autorizado"
}
```
**Confirmado**: Endpoint retorna JSON (no HTML) incluso sin autenticación ✓

### 5. Django View Logic
- **gestion_ai_config()** en views.py línea 932:
  - GET browser: renderiza template con `{% csrf_token %}`
  - GET JSON: retorna `JsonResponse` (no HTML)
  - POST: espera JSON con campo `model`, valida contra Groq, guarda en SiteConfig
- **Protección**: `_staff_required()` check pre-procesa request
- **Status**: ✓ Código correcto, deployado

### 6. Frontend Validation
- **File**: `ai_config.html` línea 258-447
- **Fixes**:
  - `getCookie('csrftoken')` con logging
  - X-CSRFToken header en POST
  - Content-Type validation pre-JSON parse
  - Error handling para non-JSON responses
  - Console logging de status/response type
- **Status**: ✓ Implementado y deployado

---

## ⏸️ BLOQUEADO: Credenciales de Producción

**Problema**: Validación del flujo completo (login → POST → persistencia) requiere:
- Username: `admin` (superusuario en Render)
- Password: `$DJANGO_SUPERUSER_PASSWORD` (env var en Render, no accesible desde local)

**Solución**: Usuario debe completar validación interactiva en navegador de producción:
1. Ir a: `https://web-matys.onrender.com/gestion-matys/login/`
2. Ingresar credenciales (super admin)
3. Navegar a: `https://web-matys.onrender.com/gestion-matys/ai/config/`
4. Abrir DevTools → Network tab
5. Verificar:
   - Cookies tab: `csrftoken` presente
   - POST a `/ai/config/`:
     - Request header: `X-CSRFToken: [token]`
     - Response: `200 application/json {success: true, ...}`
   - Cambiar modelo, recargar → persiste
6. Revisar Console: sin errores de CSRF/403/HTML parsing

---

## 📋 VALIDACIÓN PENDIENTE (Usuario)

### A. Persistencia SiteConfig
```javascript
// Consola del navegador:
// 1. Seleccionar: openai/gpt-oss-20b → Guardar
// 2. Recargar página
// 3. Verificar que modelo persiste en dropdown
// 4. Repetir con openai/gpt-oss-120b
```

### B. POST /gestion-matys/ai/tono/
```javascript
// Enviar prueba simple:
POST /gestion-matys/ai/tono/
Content-Type: application/json
X-CSRFToken: [token]

{
  "description": "Algodón de color azul marino, textura suave"
}
```
**Esperado**: `200 application/json` con `{success: true, tone: "..."}`  
**Si falla**: Revisar response status, Content-Type, body

### C. AIUsage Metrics
```
GET /gestion-matys/ai/usage/
→ Verificar tokens_used, calls_today, success_calls
```

### D. Network Tab Verification
**Ninguno de estos debería aparecer**:
- ❌ 403 Forbidden responses
- ❌ `text/html` Content-Type en respuestas
- ❌ Console errors: "Unexpected token '<'"
- ❌ "CSRF verification failed" en HTML body

---

## 🔧 Archivos Modificados

1. **web_maty/matys/templates/gestion_matys/base_admin.html**
   - Línea 514: agregado `{% csrf_token %}`
   
2. **web_maty/matys/templates/gestion_matys/ai_config.html**
   - Línea 276-323: mejorado `loadAIConfig()` con validación Content-Type
   - Línea 325-359: mejorado `loadAvailableModels()` con logging
   - Línea 374-443: mejorado POST handler con logging y validación

3. **Commit**: 8211f48

---

## ✅ Checklist de Validación

- [x] Commit 8211f48 deployado en Render
- [x] CSRF cookie generada (Set-Cookie header presente)
- [x] {% csrf_token %} en template
- [x] GET /ai/config/ retorna JSON (no HTML)
- [x] Django view logic correcto
- [x] Frontend validation implementado
- [ ] Login en producción (requiere credenciales)
- [ ] POST /ai/config/ exitoso
- [ ] SiteConfig.ai_model persiste
- [ ] POST /ai/tono/ funciona con ambos modelos
- [ ] AIUsage metrics correctas
- [ ] Console/Network sin errores CSRF/403/HTML

---

## 🎯 Próximos Pasos

1. **Usuario debe hacer login en**: `https://web-matys.onrender.com/gestion-matys/login/`
2. **Navegar a**: `https://web-matys.onrender.com/gestion-matys/ai/config/`
3. **Abrir DevTools** (F12) → Network tab
4. **Guardar modelo** (cambiar de 20b a 120b o viceversa)
5. **Verificar** en Network:
   - POST `/ai/config/` → 200, application/json, sin 403 HTML
6. **Revisar Console**: sin "Unexpected token '<'" ni CSRF errors
7. **Recargar página**: verificar modelo persiste
8. **Probar /ai/tono/**: POST con descripción simple
9. **Validar AIUsage**: `/ai/config/` GET JSON muestra tokens_used > 0

---

**Nota**: Si algún paso falla, revisar:
- Response status code
- Response Content-Type header
- Response body (primeros 200 chars)
- Browser console errors
- Django logs en Render (si tiene acceso)

Documentar y reportar cualquier error encontrado.
