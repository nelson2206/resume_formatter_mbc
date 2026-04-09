import os
import sys

# Añadir el directorio backend al path para importar el extractor
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from extractor import extraer_texto

def debug():
    filename = "CV Abel Ponte.pdf"
    if not os.path.exists(filename):
        print(f"Error: No se encuentra {filename}")
        return

    with open(filename, "rb") as f:
        file_bytes = f.read()

    print(f"--- ANALIZANDO: {filename} ({len(file_bytes)} bytes) ---")
    
    import pdfplumber
    import io
    
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            print(f"Total páginas: {len(pdf.pages)}")
            for i, page in enumerate(pdf.pages):
                chars = page.chars
                images = page.images
                print(f"Pag {i+1}: {len(chars)} caracteres, {len(images)} imágenes.")
                if len(chars) < 10 and len(images) >= 1:
                    print("  [!] Detectado: Posible PDF escaneado (muchas imágenes, poco texto seleccionable).")
    except Exception as e:
        print(f"Error abriendo PDF con pdfplumber: {e}")

    text = extraer_texto(filename, file_bytes)
    
    if not text.strip() or "" in text:
        print("\n!!! RESULTADO CRÍTICO: El texto extraído es nulo o basura ().")
        print("El PDF Abel Ponte parece ser una IMAGEN o tiene una codificación protegida.")
    else:
        print("\n--- TEXTO EXTRAIDO ---")
        print(text[:1000] + "...") # Mostrar los primeros 1000 chars

if __name__ == "__main__":
    debug()
