# Configuración Manual de Render — Sin render.yaml

## Estado Actual
- Render conectado a GitHub: `SamuelOviedo/Web-matys`
- Auto-Deploy: ❌ Deshabilitado (producción en 1324e9b, main en 9958857)
- Despliegue manual: ✓ Funciona (hemos hecho Deploy latest commit)

## Cambios Recientes (Commits pendientes)
- `d60ae3b` feat: configuración dinámica de modelo Groq + interfaz admin
- `9958857` fix: eliminar referencias a modelos obsoletos (mixtral, llama-3.1)
- Nuevos: correcciones JSON parsing + allowlist modelos compatibles

## Para Habilitar Auto-Deploy en Render Dashboard

### 1. Build Command
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

**Qué hace:**
- Instala dependencias Python
- Aplica migraciones Django (0011_update_aiusage_default_model incluida)
- Recopila archivos estáticos con WhiteNoise

### 2. Start Command
```bash
gunicorn web_maty.wsgi:application --bind 0.0.0.0:$PORT
```

**Nota:** Verificar que esto es el comando actual. Si ya funciona, mantener igual.

### 3. Environment Variables (Render Dashboard)
Verificar que están configuradas:
- `GROQ_API_KEY` = (valor de producción, nunca en Git)
- `DEBUG` = False
- `CLOUDINARY_CLOUD_NAME` = dcolpggbr
- `CLOUDINARY_API_KEY` = 747338971626437
- `CLOUDINARY_API_SECRET` = l5ESUQWFVeagqKGZIK5GnDN_RtI
- `AI_DAILY_TOKEN_LIMIT` = 10000 (opcional, si no existe usa 10000)

### 4. Cómo Habilitar Auto-Deploy
1. En Render Dashboard → Servicio → Settings
2. Buscar "Auto-Deploy"
3. Seleccionar rama: `main`
4. Habilitar "Auto-Deploy from Git"

## Seguridad: .env y Git

✓ `.env` está en `.gitignore` — no está trackeado
✓ `GROQ_API_KEY` no debe estar en Git, solo en Render env vars
✓ `.env.local` puede usarse para desarrollo local

## Flujo Actual vs Futuro

**Hoy (Manual):**
1. Hacer commit a main
2. Push a origin/main
3. Ir a Render dashboard → Deploy latest commit
4. Migraciones se aplican automáticamente (en Build Command)

**Con Auto-Deploy:**
1. Hacer commit a main
2. Push a origin/main
3. Render detecta cambios automáticamente
4. Ejecuta Build Command (migraciones incluidas)
5. Reinicia servicio

## Próximas Migraciones
- `0011_update_aiusage_default_model` — Cambiar default de AIUsage.model a 'openai/gpt-oss-20b'
- (Sin render.yaml, Build Command asegura que se ejecuten)

## Verificación Post-Deploy
- GET `/gestion-matys/ai/config/` → Debe cargar sin errores
- GET `/gestion-matys/ai/models/` → Debe devolver modelos compatibles
- POST `/gestion-matys/ai/tono/` → Debe procesar sin errores JSON
- Widget consumo IA → Debe mostrar 0 o llamadas realizadas hoy

---

**Nota:** Este documento es referencia. No modifiques Render aún sin confirmación del usuario.
