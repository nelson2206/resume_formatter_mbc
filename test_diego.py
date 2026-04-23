import sys
import os

# Forzar codificación utf-8 para la salida en consola
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, 'backend')
import extractor

# Find the file dynamically
uploads_dir = 'uploads'
file_path = None
for f in os.listdir(uploads_dir):
    if 'Diego' in f and f.endswith('.pdf'):
        file_path = os.path.join(uploads_dir, f)
        break

if not file_path:
    print("Archivo de Diego no encontrado.")
    sys.exit(1)

print(f"Archivo encontrado: {file_path}")

try:
    with open(file_path, 'rb') as f:
        content = f.read()
    
    text = extractor.extraer_texto(file_path, content)
    print('--- TEXTO EXTRAIDO ---')
    print(text[:1500])
    print('--- FIN ---')
except Exception as e:
    print(f"Error: {e}")
