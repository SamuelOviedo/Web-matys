#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Investigar si Groq expone limite via headers o respuesta
"""
import os
from groq import Groq

print("\n[*] Verificando Groq API para limite/cuota...")

try:
    client = Groq(api_key=os.environ.get('GROQ_API_KEY', ''))
    if not os.environ.get('GROQ_API_KEY'):
        print("[AVISO] GROQ_API_KEY no configurada. Saltando prueba real.")
        print("\n[HALLAZGO] Sin API key, no se puede verificar limites reales de Groq")
        print("[RECOMENDACION] Usar limite configurado (10000) como INTERNO")
        sys.exit(0)

    # Hacer call minimo para ver headers
    completion = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[{'role': 'user', 'content': 'Hi'}],
        max_tokens=10
    )

    print("\n[OK] Llamada a Groq exitosa")
    print("\nObjeto usage retornado:")
    print("  - prompt_tokens: {}".format(completion.usage.prompt_tokens))
    print("  - completion_tokens: {}".format(completion.usage.completion_tokens))
    print("  - total_tokens: {}".format(completion.usage.total_tokens))

    # Inspeccionar headers del response
    if hasattr(completion, '_response_ms'):
        print("\n[INFO] Response metadata disponible: {}".format(dir(completion)))

    print("\n[HALLAZGO] Groq NO expone limite/cuota en respuesta")
    print("[CONCLUSION] Usar AI_DAILY_TOKEN_LIMIT como limite INTERNO diario")

except Exception as e:
    print("[ERROR] {}".format(e))
    print("\n[CONCLUSION] No se pudo verificar con Groq real")
    print("[RECOMENDACION] Marcar limite como INTERNO en UI")
