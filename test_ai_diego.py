import sys
import os
import json

# Forzar codificación utf-8
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'backend')

import ai_service

try:
    with open('output_diego.txt', 'r', encoding='utf-8', errors='ignore') as f:
        texto_cv = f.read()

    print("Enviando a OpenAI...")
    resultado = ai_service.extrae_perfil_cv(texto_cv)
    print("--- RESULTADO DE LA IA ---")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
