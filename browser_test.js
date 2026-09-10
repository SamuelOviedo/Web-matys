/**
 * Script de prueba para validación manual en navegador
 * Ejecutar en DevTools console en: https://web-matys.onrender.com/gestion-matys/ai/config/
 *
 * Pasos:
 * 1. Hacer login en /gestion-matys/login/
 * 2. Navegar a /gestion-matys/ai/config/
 * 3. Abrir DevTools (F12)
 * 4. Ir a Console
 * 5. Copiar y pegar el siguiente código
 */

(async function validateCSRFandPost() {
  console.log("=".repeat(70));
  console.log("VALIDACIÓN: POST /gestion-matys/ai/config/");
  console.log("=".repeat(70));

  // 1. Verificar CSRF cookie
  console.log("\n[1] Verificar CSRF cookie...");
  const csrftoken = document.querySelector('[name=csrftoken]')?.value ||
                    new URLSearchParams(document.cookie.split('; ').join('&')).get('csrftoken');

  if (!csrftoken) {
    console.error("❌ CSRF token NO ENCONTRADO en meta tag o cookie");
    return;
  }
  console.log("✓ CSRF token encontrado:", csrftoken.substring(0, 20) + "...");

  // 2. Obtener modelo actual
  console.log("\n[2] GET /ai/config/ (config actual)...");
  const configRes = await fetch('/gestion-matys/ai/config/', {
    headers: { 'Accept': 'application/json' }
  });

  if (configRes.status !== 200) {
    console.error(`❌ GET failed: ${configRes.status}`);
    return;
  }

  const configData = await configRes.json();
  const currentModel = configData.ai_model;
  console.log("✓ Modelo actual:", currentModel);

  // 3. Seleccionar nuevo modelo
  console.log("\n[3] Seleccionar modelo para cambiar...");
  const newModel = currentModel === 'openai/gpt-oss-20b'
    ? 'openai/gpt-oss-120b'
    : 'openai/gpt-oss-20b';
  console.log("  Cambiar de:", currentModel);
  console.log("  Cambiar a:", newModel);

  // 4. POST /ai/config/ con nuevo modelo
  console.log("\n[4] POST /ai/config/ con X-CSRFToken header...");
  const postRes = await fetch('/gestion-matys/ai/config/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ model: newModel })
  });

  console.log("  HTTP Status:", postRes.status);
  console.log("  Content-Type:", postRes.headers.get('Content-Type'));

  if (postRes.status !== 200) {
    console.error(`❌ POST failed: ${postRes.status}`);
    const body = await postRes.text();
    console.error("  Response (primeros 200 chars):", body.substring(0, 200));
    return;
  }

  const contentType = postRes.headers.get('Content-Type') || '';
  if (!contentType.includes('application/json')) {
    console.error(`❌ Content-Type no es JSON: ${contentType}`);
    return;
  }

  const postData = await postRes.json();
  if (!postData.success) {
    console.error("❌ POST no exitoso:", postData.error);
    return;
  }

  console.log("✓ POST exitoso, modelo guardado:", postData.ai_model);

  // 5. Verificar persistencia
  console.log("\n[5] Verificar persistencia (recargar config)...");
  const reloadRes = await fetch('/gestion-matys/ai/config/', {
    headers: { 'Accept': 'application/json' }
  });

  if (reloadRes.status !== 200) {
    console.error(`❌ Reload failed: ${reloadRes.status}`);
    return;
  }

  const reloadData = await reloadRes.json();
  const persistedModel = reloadData.ai_model;

  if (persistedModel !== newModel) {
    console.error(`❌ Modelo NO persiste. Esperado: ${newModel}, Actual: ${persistedModel}`);
    return;
  }

  console.log("✓ Modelo persiste después de recargar:", persistedModel);

  // 6. Verificar AIUsage
  console.log("\n[6] Verificar AIUsage metrics...");
  const usageRes = await fetch('/gestion-matys/ai/config/', {
    headers: { 'Accept': 'application/json' }
  });
  const usageData = await usageRes.json();
  console.log("  Tokens usados hoy:", usageData.tokens_used);
  console.log("  Llamadas hoy:", usageData.calls_today);
  console.log("  Porcentaje:", usageData.percentage + "%");

  console.log("\n" + "=".repeat(70));
  console.log("✓ VALIDACIÓN EXITOSA");
  console.log("=".repeat(70));
  console.log("Resumen:");
  console.log("  - CSRF token presente ✓");
  console.log("  - POST /ai/config/ retorna 200 JSON ✓");
  console.log("  - Modelo " + currentModel + " → " + newModel + " guardado ✓");
  console.log("  - Persistencia verificada ✓");
  console.log("  - Sin errores CSRF/403/HTML ✓");
})();
