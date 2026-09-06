"""
main.py — API FastAPI para el Staffing AI Builder.

Endpoints:
  GET  /api/health         → Estado del servidor
  POST /api/procesar       → Procesa uno o múltiples CVs y devuelve metadata
  GET  /api/descargar/{id} → Descarga un PPT específico
  GET  /api/descargar-zip  → Descarga ZIP con todos los PPTs de la sesión
"""

import os
import base64
import traceback
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from extractor import extraer_texto, extraer_imagenes_pdf, MARCA_ESCANEADO
from ai_service import extrae_perfil_cv
from normalizer import normalizar_perfil
from ppt_builder import generar_ppt_desde_plantilla
from file_manager import (
    inicializar_directorios,
    guardar_upload_temporal,
    nombre_salida_ppt,
    crear_zip,
    limpiar_archivo,
)
from config import CV_EXTENSIONS_PERMITIDAS, OUTPUTS_DIR, UPLOADS_DIR

# ── Inicialización ─────────────────────────────────────────────────────────────
inicializar_directorios()

app = FastAPI(title="Staffing AI Builder", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sesión en memoria: guarda rutas de PPTs generados (para el ZIP)
_sesion_ppts: list = []


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    """Verifica que el backend está activo."""
    return {"status": "ok", "version": "2.0"}


@app.post("/api/procesar")
async def procesar_documentos(
    background_tasks: BackgroundTasks,
    cvs: List[UploadFile] = File(...),
    plantilla: Optional[UploadFile] = File(None),
    contexto: str = Form(""),
    idioma: str = Form("es"),
    formato: str = Form("sin_empresa"),
    proveedor: str = Form("gemini"),
):
    """
    Procesa uno o múltiples CVs. Si no se envía plantilla, usa la cargada por defecto.
    """
    global _sesion_ppts
    _sesion_ppts = []

    DEFAULT_TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "templates", "CV template.pptx")

    if plantilla:
        plantilla_bytes = await plantilla.read()
        plantilla_path = guardar_upload_temporal(plantilla.filename, plantilla_bytes)
        es_temporal = True
    else:
        if not os.path.exists(DEFAULT_TEMPLATE):
            raise ValueError(f"Falta plantilla y no se encontró {DEFAULT_TEMPLATE}")
        plantilla_path = DEFAULT_TEMPLATE
        es_temporal = False

    resultados = []

    for cv_file in cvs:
        resultado = {
            "archivo": cv_file.filename,
            "estado": "ok",
            "nombre": "",
            "rol_seniority": "",
            "alertas": [],
            "ppt_id": None,
            "error": None,
        }

        cv_path = None
        output_path = None

        try:
            # ── Validar extensión ──────────────────────────────────────────────
            ext = "." + cv_file.filename.rsplit(".", 1)[-1].lower() if "." in cv_file.filename else ""
            if ext not in CV_EXTENSIONS_PERMITIDAS:
                raise ValueError(f"Formato '{ext}' no soportado. Usa PDF, DOCX o TXT.")

            # ── Leer y extraer texto del CV ────────────────────────────────────
            cv_bytes = await cv_file.read()
            cv_path = guardar_upload_temporal(cv_file.filename, cv_bytes)
            texto_cv = extraer_texto(cv_file.filename, cv_bytes)

            # ── PDF escaneado: leerlo con la vision del modelo ─────────────────
            # Si el PDF no tiene texto util, se renderizan sus paginas a imagen y
            # se envian al modelo multimodal, que ademas entiende el layout.
            imagenes_cv = None
            if ext == ".pdf" and (texto_cv.startswith(MARCA_ESCANEADO) or len(texto_cv.strip()) < 30):
                imagenes_cv = extraer_imagenes_pdf(cv_bytes)
                if imagenes_cv:
                    texto_cv = ""

            if not imagenes_cv and len(texto_cv.strip()) < 30:
                raise ValueError("No se pudo extraer texto suficiente del CV. Verifica que el archivo no este vacio o protegido.")

            # ── Extraer perfil con IA ──────────────────────────────────────────
            datos_raw = extrae_perfil_cv(texto_cv, contexto, idioma, formato, proveedor, imagenes_cv)

            # ── Normalizar y validar ───────────────────────────────────────────
            perfil = normalizar_perfil(datos_raw)

            # ── Generar PPT ────────────────────────────────────────────────────
            output_path = nombre_salida_ppt(perfil.get("nombre", "Consultor"))
            generar_ppt_desde_plantilla(plantilla_path, output_path, perfil)

            # ── Registrar resultado ────────────────────────────────────────────
            ppt_id = os.path.basename(output_path)
            _sesion_ppts.append(output_path)

            # Embebemos el PPTX en base64 para que el frontend lo descargue sin
            # depender del disco (Render Free es efímero y se borra en cada redeploy).
            with open(output_path, "rb") as _f:
                ppt_b64 = base64.b64encode(_f.read()).decode("ascii")

            resultado["nombre"] = perfil.get("nombre", "")
            resultado["rol_seniority"] = perfil.get("rol_seniority", "")
            resultado["enfoque_fit"] = perfil.get("enfoque_fit", "")
            resultado["fit_score"] = perfil.get("fit_score", 0)
            resultado["semaforo"] = perfil.get("semaforo", {"cumple": [], "gaps": []})
            resultado["alertas"] = perfil.get("alertas", [])
            if imagenes_cv:
                resultado["alertas"].append(
                    "CV escaneado: leido visualmente por la IA (%d pagina(s))." % len(imagenes_cv)
                )
            resultado["ppt_id"] = ppt_id
            resultado["ppt_base64"] = ppt_b64  # Para descarga directa sin tocar disco
            resultado["cv_id"] = os.path.basename(cv_path)
            resultado["perfil"] = perfil # Data completa para previsualización HTML

        except Exception as e:
            resultado["estado"] = "error"
            resultado["error"] = str(e)
            # Loguear detalle del error
            with open(os.path.join(os.path.dirname(__file__), "error.log"), "a", encoding="utf-8") as f:
                f.write(f"\n--- ERROR procesando {cv_file.filename} ---\n")
                f.write(traceback.format_exc() + "\n")
        finally:
            # Limpiar CV temporal (COMENTADO para permitir previsualización durante la sesión)
            # if cv_path:
            #     background_tasks.add_task(limpiar_archivo, cv_path)
            pass

        resultados.append(resultado)

    # Limpiar plantilla temporal
    if es_temporal:
        background_tasks.add_task(limpiar_archivo, plantilla_path)

    return JSONResponse(content={"resultados": resultados})


@app.get("/api/cv/{filename}")
async def ver_cv(filename: str):
    """Sirve un CV original para previsualización."""
    # Seguridad: solo el nombre del archivo, sin rutas
    safe_name = os.path.basename(filename)
    # Forzar ruta absoluta para evitar problemas de contexto
    ABS_UPLOADS = os.path.abspath(UPLOADS_DIR)
    file_path = os.path.join(ABS_UPLOADS, safe_name)
    
    if not os.path.exists(file_path):
        print(f"[preview] Archivo no encontrado en: {file_path}")
        raise HTTPException(status_code=404, detail="CV no encontrado.")
    
    # Determinar media type correcto para evitar errores de previsualización
    media_type = "application/pdf"
    if safe_name.lower().endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif safe_name.lower().endswith(".doc"):
        media_type = "application/msword"
    elif safe_name.lower().endswith(".pptx"):
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    elif safe_name.lower().endswith(".txt"):
        media_type = "text/plain"
    
    return FileResponse(
        file_path, 
        media_type=media_type,
        filename=safe_name,  # Ayuda al navegador a identificar la descarga si no puede previsualizar
        content_disposition_type="inline"
    )


@app.get("/api/descargar/{ppt_id}")
def descargar_ppt(ppt_id: str):
    """
    Descarga un PPT individual por su ID (nombre de archivo).
    """
    # Seguridad: solo el nombre del archivo, sin rutas
    safe_id = os.path.basename(ppt_id)
    ruta = os.path.join(OUTPUTS_DIR, safe_id)

    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")

    return FileResponse(
        ruta,
        filename=safe_id,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@app.get("/api/descargar-zip")
def descargar_zip():
    """
    Empaqueta todos los PPTs de la sesión actual en un ZIP y lo descarga.
    """
    global _sesion_ppts

    if not _sesion_ppts:
        raise HTTPException(status_code=404, detail="No hay archivos generados en la sesión actual.")

    zip_path = crear_zip(_sesion_ppts)

    return FileResponse(
        zip_path,
        filename="Perfiles_Generados.zip",
        media_type="application/zip",
    )
