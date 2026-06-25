"""
config.py — Configuración centralizada del sistema Staffing AI Builder
"""

# Directorio base del backend (relativo a este archivo)
import os
from dotenv import load_dotenv

# Cargamos .env aquí también para que los overrides de modelo por variable de
# entorno estén disponibles al construir PROVEEDORES (config se importa primero).
load_dotenv(override=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Directorios de trabajo
TEMPLATES_DIR = os.path.join(PROJECT_DIR, "templates")
OUTPUTS_DIR = os.path.join(PROJECT_DIR, "outputs")
UPLOADS_DIR = os.path.join(PROJECT_DIR, "uploads")

# Temperatura compartida por todos los proveedores (baja = máxima precisión documental).
LLM_TEMPERATURE = 0.15

# ── Proveedores de IA disponibles ───────────────────────────────────────────────
# El usuario elige uno en la UI. Cada proveedor define:
#   - label: nombre visible en el frontend
#   - model: ID del modelo (overridable con la variable de entorno indicada en 'model_env')
#   - env:   variable de entorno con la API key
# El modelo se puede cambiar sin tocar código vía las variables OPENAI_MODEL /
# GEMINI_MODEL / ANTHROPIC_MODEL en el .env.
PROVEEDORES = {
    "openai": {
        "label": "OpenAI",
        "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        "env": "OPENAI_API_KEY",
    },
    "gemini": {
        "label": "Google Gemini",
        # gemini-2.5-flash (GA): estable y fiable. gemini-3.5-flash es más nuevo pero
        # hoy tiene capacidad saturada (503 frecuentes). Cambia con GEMINI_MODEL si quieres
        # probar el más reciente cuando se estabilice.
        "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "env": "GEMINI_API_KEY",
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        "env": "ANTHROPIC_API_KEY",
    },
    "groq": {
        "label": "Groq",
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "env": "GROQ_API_KEY",
    },
}
PROVEEDOR_DEFAULT = "gemini"

# Compatibilidad: algunos módulos/tests aún referencian LLM_MODEL.
LLM_MODEL = PROVEEDORES["openai"]["model"]

# Categorías de seniority válidas (Big4)
SENIORITY_LEVELS = [
    "Analyst",
    "Consultant",
    "Senior Consultant",
    "Manager",
    "Senior Manager",
    "Director",
    "Por validar",
]

# Idiomas soportados
IDIOMAS_SOPORTADOS = {
    "es": "Español",
    "en": "English",
}

# Formatos de redacción de la experiencia profesional
#   "con_empresa": cada bullet inicia con el nombre de la empresa/cliente (tal como aparece en el CV).
#   "sin_empresa": no se nombra la empresa; se describe la actividad y se referencia el tipo/sector.
FORMATOS_EXPERIENCIA = ("con_empresa", "sin_empresa")
FORMATO_EXPERIENCIA_DEFAULT = "sin_empresa"

# Extensiones de archivo permitidas para CVs
CV_EXTENSIONS_PERMITIDAS = {".pdf", ".docx", ".doc", ".txt", ".pptx"}

# Mapeo de shapes en la plantilla PPT (por nombre/índice/rol)
# Estos índices corresponden a la plantilla analizada "CV Eva Rodriguez.pptx"
# Si el usuario cambia la plantilla, estos valores deben actualizarse.
SHAPE_MAP = {
    "nombre_rol": {
        "shape_name": "Título 1",          # Shape 5
        "paragraph_idx": 0,                 # Único párrafo con \x0b separador
        "separator": "\x0b",               # Salto vertical entre Nombre y Rol/Seniority
    },
    "resumen_y_experiencia": {
        "shape_name": "Rectángulo 8",       # Shape 7
        "resumen_paragraph_idx": 0,         # Párrafo 0 = Resumen profesional
        "separador_paragraph_idx": 1,       # Párrafo 1 = línea vacía (mantener)
        "experiencia_start_idx": 2,         # Párrafos 2-N = Bullets de experiencia
    },
    "formacion": {
        "shape_name": "object 9",           # Shape 8
        "label_paragraph_idx": 0,           # "Formación académica" — NO tocar
        "content_paragraph_idx": 1,         # Párrafo 1 = contenido
    },
    "idiomas": {
        "shape_name": "object 10",          # Shape 9 (primer shape con ese nombre)
        "label_paragraph_idx": 0,           # "Idiomas" — NO tocar
        "content_paragraph_idx": 1,         # Párrafo 1 = contenido
    },
    "conocimientos": {
        "shape_name": "object 10",          # Shape 10 (segundo shape con ese nombre)
        "label_paragraph_idx": 0,           # "Conocimientos Clave" — NO tocar
        "content_start_idx": 1,             # Párrafo 1-N = bullets
    },
}
