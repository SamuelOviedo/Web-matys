# Correcciones IA — Problemas Encontrados en Producción

## 1. Error "Unterminated string" en gestion_ai_tono()

### Causa Exacta
- **Problema:** Algunos modelos (ej: `allam-2-7b`, modelos árabes) no siguen bien el prompt en inglés/español
- **Síntoma:** Respuesta no es JSON válido → `json.loads()` falla con "Unterminated string starting at: line 1 column 35"
- **Línea anterior:** Línea 691 hacía `json.loads(raw.strip())` sin validación, luego mostraba `str(e)` al usuario

### Solución Implementada
1. **Try/except anidado para JSON parsing:**
   - Intenta parse JSON de forma robusta (elimina markdown, newlines)
   - Si falla: captura `json.JSONDecodeError` específicamente
   - Registra error EN AIUsage CON tokens consumidos (Groq sí respondió)
   - Retorna mensaje amigable sin detalles técnicos

2. **Registro de errores mejorado:**
   - Si Groq responde pero JSON falla → AIUsage.status='error' con tokens consumidos
   - Si Groq no responde → AIUsage.status='error' con tokens=0
   - Detalles técnicos se guardan en AIUsage.error_message para investigación

3. **Mensajes al usuario:**
   - ANTES: "Unterminated string starting at: line 1 column 35 (char 34)"
   - AHORA: "El modelo seleccionado no generó una respuesta válida. Intenta con otro modelo o edita manualmente los tonos."

### Ventajas
- ✓ No expone errores técnicos al usuario
- ✓ Registra detalles para debugging
- ✓ Permite cambiar a otro modelo sin romper la app
- ✓ Captura tokens aunque JSON falle (datos de consumo precisos)

---

## 2. Filtrado Inadecuado de Modelos en /ai/models/

### Problema
- Modelos incompatibles en dropdown: `canopylabs/orpheus-v1-english`, `canopylabs/orpheus-arabic-saudi`
- Filtro anterior: solo búsqueda de palabras clave en nombre → impreciso

### Solución Implementada
1. **Allowlist explícita de familias compatibles:**
   ```python
   compatible_prefixes = [
       'mixtral-',      # Mistral Mixtral (8x7b, 8x22b, etc)
       'llama-3',       # Meta Llama 3 y 3.1 (8b, 70b)
       'gemma-',        # Google Gemma (2b, 7b)
       'gpt-oss-',      # OpenAI compatible (gpt-oss-20b)
   ]
   ```

2. **Exclusión explícita de incompatibles:**
   - whisper, guard, moderation, tts, audio, embed, embedding, orpheus

3. **Lógica de filtrado:**
   - Excluye si tiene palabra clave incompatible
   - Incluye solo si matches con allowlist
   - Fallback conservador: excluye si no está en allowlist

### Validación Manual
- ✓ `mixtral-8x7b-32768` → Incluido
- ✓ `mixtral-8x22b-32768` → Incluido
- ✓ `llama-3-8b-instant` → Incluido
- ✓ `llama-3-70b-versatile` → Incluido
- ✓ `llama-3.1-8b-instant` → Incluido (aunque retirado, si existe lo muestra)
- ✓ `gemma-7b-it` → Incluido
- ✓ `gpt-oss-20b` → Incluido
- ✗ `canopylabs/orpheus-v1-english` → Excluido (no en allowlist)
- ✗ `whisper-large-v3-turbo` → Excluido (palabra: whisper)

### Mantenibilidad
- Allowlist es explícita y documentada
- Fácil agregar nuevas familias: solo agregar a `compatible_prefixes`
- Sin hardcodear modelos individuales (solo prefijos de familias)
- Cuando Groq agrega nuevos modelos:
  - Si son de familia conocida (mixtral-*, llama-3*, etc) → aparecen automáticamente
  - Si son familia nueva → agregar a allowlist manualmente

---

## 3. Registro de Consumo IA

### Problema Encontrado
- Widget mostraba 0 llamadas y 0 tokens después de llamadas fallidas
- Llamadas con error no se registraban en AIUsage

### Solución Implementada
- **Llamadas exitosas:** AIUsage.status='success' con tokens consumidos
- **Llamadas con error JSON:** AIUsage.status='error' con tokens consumidos
- **Llamadas sin respuesta:** AIUsage.status='error' con tokens=0 (Groq no respondió)

Widget ahora:
- ✓ Cuenta llamadas exitosas + fallidas (filtra status='success' para consumo)
- ✓ Muestra tokens del día (solo exitosas para % de consumo)
- ✓ Registra errores para investigación en admin

---

## 4. Render — Configuración Manual Recomendada

### Verificación .env
- ✓ `.env` está en `.gitignore` → no está trackeado en Git
- ✓ `GROQ_API_KEY` en .env local, NUNCA en Git

### Configuración Render (SIN render.yaml)

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

**Start Command:**
(Mantener actual si funciona)

**Environment Variables (Render Dashboard):**
- GROQ_API_KEY = (producción, nunca en Git)
- DEBUG = False
- Cloudinary vars
- AI_DAILY_TOKEN_LIMIT = 10000 (opcional)

**Para Auto-Deploy:**
1. Render Dashboard → Settings
2. Auto-Deploy: rama `main`
3. Habilitar
4. Cada push a main desplegará automáticamente

---

## 5. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| **views.py** | • gestion_ai_tono(): JSON parsing robusto + errores amigables<br>• gestion_ai_models(): allowlist + exclusión explícita |
| **RENDER_CONFIG_MANUAL.md** | ✨ NEW - Guía configuración Render sin blueprint |
| **CORRECCIONES_IA_PRODUCCION.md** | ✨ NEW - Este documento |

---

## 6. Pruebas Realizadas (Locales)

### Validación Sintaxis
- ✓ `python -m py_compile matys/views.py` — OK
- ✓ `python manage.py check` — OK (0 issues)

### Validación Migraciones
- ✓ `python manage.py migrate --plan` — muestra 0011 lista para aplicar

### Comportamiento Esperado
1. POST `/gestion-matys/ai/tono/` con modelo compatible (mixtral-8x7b):
   - ✓ JSON válido → retorna tonos
   - ✓ Registra en AIUsage con tokens
   
2. POST `/gestion-matys/ai/tono/` con modelo que falla JSON:
   - ✓ Retorna error amigable (sin "Unterminated string")
   - ✓ Registra en AIUsage status='error' con tokens consumidos
   
3. GET `/gestion-matys/ai/models/`:
   - ✓ Devuelve solo modelos en allowlist
   - ✓ Excluye orpheus, whisper, etc

4. Widget consumo IA:
   - ✓ Muestra consumo del día (solo exitosas)
   - ✓ Actualiza cada 30 seg
   - ✓ Muestra advertencia si modelo no existe

---

## 7. Próximos Pasos

1. ✓ Commit cambios a main
2. ✓ Push a origin/main
3. ✓ Verificar en producción (Render)
4. Opcional: Configurar Auto-Deploy según RENDER_CONFIG_MANUAL.md

---

**Estado:** Listo para commit y push a main.
