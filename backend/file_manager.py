"""
file_manager.py — Gestión de archivos temporales, uploads y outputs.
"""

import os
import zipfile
import tempfile
import shutil
from datetime import datetime
from config import OUTPUTS_DIR, UPLOADS_DIR


def inicializar_directorios():
    """Crea los directorios necesarios si no existen."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)


def guardar_upload_temporal(filename: str, file_bytes: bytes) -> str:
    """Guarda un archivo cargado en el directorio temporal y devuelve la ruta."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    # Usar nombre seguro con timestamp para evitar colisiones
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = f"{ts}_{filename.replace(' ', '_')}"
    ruta = os.path.join(UPLOADS_DIR, safe_name)
    with open(ruta, "wb") as f:
        f.write(file_bytes)
    return ruta


def nombre_salida_ppt(nombre_consultor: str) -> str:
    """Genera un nombre de archivo de salida limpio para el PPT."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Limpiar caracteres no permitidos en nombre de archivo
    nombre_limpio = "".join(c for c in nombre_consultor if c.isalnum() or c in " _-").strip()
    nombre_limpio = nombre_limpio.replace(" ", "_") or "Consultor"
    filename = f"Perfil_{nombre_limpio}_{ts}.pptx"
    return os.path.join(OUTPUTS_DIR, filename)


def crear_zip(rutas_pptx: list, nombre_zip: str = "Perfiles_Generados.zip") -> str:
    """
    Empaqueta múltiples archivos .pptx en un ZIP.
    Devuelve la ruta del ZIP generado.
    """
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(OUTPUTS_DIR, f"{ts}_{nombre_zip}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for ruta in rutas_pptx:
            if os.path.exists(ruta):
                zf.write(ruta, arcname=os.path.basename(ruta))
    return zip_path


def limpiar_archivo(ruta: str):
    """Elimina un archivo temporal de forma segura."""
    try:
        if ruta and os.path.exists(ruta):
            os.remove(ruta)
    except Exception as e:
        print(f"[file_manager] No se pudo eliminar '{ruta}': {e}")
