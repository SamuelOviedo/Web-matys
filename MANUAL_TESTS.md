# Validación Manual Final — Tours + Widget IA

**Estado actual:** Código listo. Falta validación en navegador.

**Fecha inicio:** 2026-09-10
**Responsable:** [Usuario]

---

## 1. SETUP

```bash
cd "C:\MultiStack Systems\Projects\Web-matys\web_maty"
python manage.py runserver
# Acceder a: http://localhost:8000/gestion-matys/
```

**Credenciales admin:**
- Usuario: admin
- Pass: admin123 (o lo que esté configurado)

---

## 2. TOURS — DESKTOP

### 2.1 Recorrido General Panel
1. Abrir http://localhost:8000/gestion-matys/
2. Click en icono "compass" o buscar "Recorrido general"
3. **Verificar cada paso:**
   - [ ] PASO 1: Logo sidebar — modal aparece en posición CORRECTA (no parpadea)
   - [ ] PASO 2: Dashboard — modal sin salto
   - [ ] PASO 3: Categorías — modal sin salto
   - [ ] PASO 4: Inicio (textos) — modal sin salto
   - [ ] PASO 5: Imágenes — modal sin salto
   - [ ] PASO 6: Ayuda — modal sin salto
4. **Botones:**
   - [ ] "Siguiente" avanza sin flickering
   - [ ] "Anterior" retrocede sin flickering
   - [ ] "Cerrar" cierra sin errores
5. **Posicionamiento especial:**
   - [ ] Si modal aparece en borde de pantalla, se reposiciona suavemente (NO salto)
   - [ ] Contenido readable en todos los casos

### 2.2 Otros Tours (si existen)
- [ ] Ejecutar cada tour disponible en "Centro de ayuda"
- [ ] Verificar posicionamiento similar

---

## 3. TOURS — RESPONSIVE (Mobile)

1. F12 → Toggle device toolbar
2. Simular iPhone 12 (390x844)
3. Repetir recorrido general:
   - [ ] Sidebar abre/cierra correctamente
   - [ ] Modal se posiciona adecuadamente en pantalla angosta
   - [ ] No hay overflow/contenido cortado
   - [ ] Navegación touch-friendly
4. Probar en iPad (768x1024):
   - [ ] Modal adapta a viewport
   - [ ] Botones accesibles

---

## 4. WIDGET IA — Estado 0 (sin consumo)

1. Limpiar base de datos de AIUsage (si hay registros viejos)
2. Abrir dashboard fresco
3. **Verificar:**
   - [ ] Widget NO se muestra (display:none correcto)
   - [ ] Dashboard limpio, sin elementos extraños
   - [ ] Consola sin errores (F12 → Console)

---

## 5. WIDGET IA — Generar Consumo Real

1. En dashboard, ir a "Prendas" → crear nueva prenda:
   - Nombre: "Test Consumo IA"
   - Descripción corta: "Vestido elegante de noche color negro"
   - Otros datos: llenar minimo requerido
2. **Usar AI Tone:**
   - Click "Generar tonos IA" o similar
   - Esperar a que procese (2-5 seg)
3. **Verificar Widget:**
   - [ ] Widget AHORA se muestra (display:block)
   - [ ] Muestra porcentaje (ej: "2%")
   - [ ] Muestra tokens: "X / 10000"
   - [ ] Barra de progreso visible y correcta
   - [ ] Label dice "Consumo IA (límite interno)" ← **CRÍTICO**
4. **Verificar datos:**
   - [ ] Porcentaje = tokens_used / 10000 * 100
   - [ ] Llamadas_hoy incremento correctamente
   - [ ] Colores normales (navy/blue) ya que < 50%

**Test adicional:** Hacer 2-3 solicitudes IA más
- [ ] Widget actualiza cada vez (refesh automático o manual)
- [ ] Tokens acumulan correctamente

---

## 6. WIDGET IA — Estados Críticos

### 6.1 Bajo Consumo (~25%)
1. Generar hasta ~2500 tokens de consumo
2. **Verificar:**
   - [ ] Widget visible (>= 25% umbral)
   - [ ] Porcentaje ≈ 25%
   - [ ] Barra al 25%
   - [ ] Color: navy/blue (normal)

### 6.2 Consumo Medio-Alto (~60%)
1. Generar hasta ~6000 tokens
2. **Verificar:**
   - [ ] Porcentaje ≈ 60%
   - [ ] Barra al 60%
   - [ ] Color: gradiente navy→blue claro (50-80%)

### 6.3 Consumo Crítico (>80%)
1. Generar hasta ~8500+ tokens
2. **Verificar:**
   - [ ] Porcentaje > 80%
   - [ ] Barra al 80%+
   - [ ] **Color CAMBIA a naranja/amarillo** ← gradiente naranja
   - [ ] Porcentaje texto en NARANJA también
   - [ ] Visual alert clara

### 6.4 Límite Alcanzado/Superado (>=100%)
1. Generar solicitudes hasta >=10000 tokens
2. **Verificar:**
   - [ ] Porcentaje tapa en 100% (máximo)
   - [ ] Barra al 100%
   - [ ] Color: rojo/naranja intenso
   - [ ] No muestra >100% (js limita a min(pct, 100))

---

## 7. WIDGET IA — Fallback/Errores

### 7.1 Endpoint No Responde
1. Pausar servidor momentáneamente
2. Recargar dashboard
3. **Verificar:**
   - [ ] Widget intenta cargar pero falla silenciosamente
   - [ ] Consola muestra log (no error bloqueante): "AI usage widget load error"
   - [ ] Dashboard sigue funcional
   - [ ] No popup de error al usuario

### 7.2 Respuesta Inválida
1. (Simulación) Editar response en browser dev tools (si es posible)
2. O generar llamada IA sin estar autenticado
3. **Verificar:**
   - [ ] Widget no se muestra
   - [ ] Panel sigue operativo
   - [ ] No errores en navegación

---

## 8. TOURS + WIDGET — Interacción

1. Abrir tour con widget visible
2. **Verificar:**
   - [ ] Tour modal se superpone correctamente
   - [ ] Widget no interfiere con tour
   - [ ] z-index correcto (tour encima)
3. Navegar tour mientras widget en pantalla:
   - [ ] Ambos elementos responden bien

---

## 9. EDGE CASES

- [ ] Números de tokens grandes (>1M): se formatean con toLocaleString() ✓
- [ ] Cambio de zona horaria: límite diario sigue siendo "hoy" UTC
- [ ] Múltiples tabs abiertas: cada tab hace fetch propio (OK)
- [ ] Offline: widget falla gracefully ✓

---

## 10. CHECKLIST FINAL PRE-PRODUCCIÓN

```
Tours:
  [_] Desktop: 6+ tours sin saltos visuales
  [_] Responsive: mobile y tablet sin issues
  [_] Anterior/Siguiente sin flickering
  [_] Posicionamiento edge cases OK

Widget IA:
  [_] Estado 0: no se muestra (correcto)
  [_] Consumo real: actualiza correctamente
  [_] Label: "límite interno" visible
  [_] Bajo consumo (25%): navy/blue ✓
  [_] Medio (60%): gradiente ✓
  [_] Alto (>80%): naranja/amarillo ✓
  [_] Límite (100%): capped, color intense ✓
  [_] Fallback: error silencioso, panel OK ✓

Código:
  [_] Migración aplicada
  [_] Sin errores consola
  [_] Sin errores servidor
  [_] Commits pusheados a main
```

---

## Resultado Final

**Fecha completado:** ____________

**Responsable:** ____________

**Estado:** 
- [ ] TODO — Pruebas pendientes
- [ ] EN PROGRESO
- [ ] ✓ LISTO PARA PRODUCCIÓN

**Notas:**
```
[Dejar aquí cualquier hallazgo o ajuste necesario]
```

---

**PRÓXIMO PASO:** Si ✓ en todos, mergear a producción y documentar.
