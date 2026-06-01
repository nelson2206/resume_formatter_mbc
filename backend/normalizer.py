"""
normalizer.py — Normaliza y valida el JSON de perfil extraído por la IA.
Garantiza que todos los campos existen y tienen tipos correctos antes de continuar.
"""

from config import SENIORITY_LEVELS


def normalizar_perfil(datos: dict) -> dict:
    """
    Valida y normaliza el diccionario de perfil devuelto por la IA.
    Asegura que todos los campos existen, tienen el tipo correcto,
    y que el seniority es una categoría reconocida.
    """

    perfil = {
        "nombre": _str(datos.get("nombre", "")),
        "rol_seniority": _str(datos.get("rol_seniority", "")),
        "enfoque_fit": _str(datos.get("enfoque_fit", "")),
        "formacion_academica": _lista(datos.get("formacion_academica", [])),
        "conocimientos_clave": _lista(datos.get("conocimientos_clave", [])),
        "idiomas": _str(datos.get("idiomas", "")),
        "resumen_profesional": _str(datos.get("resumen_profesional", "")),
        "experiencia_profesional": _lista(datos.get("experiencia_profesional", [])),
        "fit_score": _fit_score(datos.get("fit_score")),
        "semaforo": datos.get("semaforo", {"cumple": [], "gaps": []}),
        "alertas": _lista(datos.get("alertas", [])),
    }

    # Forzar términos en inglés para seniority (como pidió el usuario)
    rol_lower = perfil["rol_seniority"].lower()
    mapping = {
        "analista": "Analyst",
        "consultor senior": "Senior Consultant",
        "consultor": "Consultant",
        "gerente": "Manager",
        "director": "Director"
    }
    for es, en in mapping.items():
        if es in rol_lower:
            # Reemplazo respetando el contexto si es posible, o directo
            perfil["rol_seniority"] = perfil["rol_seniority"].replace(es.capitalize(), en).replace(es, en)

    # Validar que el seniority sea reconocido
    rol_seniority = perfil["rol_seniority"]
    seniority_detectado = False
    for nivel in SENIORITY_LEVELS:
        if nivel.lower() in rol_seniority.lower() and nivel != "Por validar":
            seniority_detectado = True
            break

    if not seniority_detectado and rol_seniority:
        perfil["alertas"].append(
            "Seniority sugerido podría no coincidir con categorías estándar Minsait. Revisa la salida."
        )

    # Alertas por campos vacíos críticos
    if not perfil["nombre"]:
        perfil["alertas"].append("Nombre no encontrado en el CV.")

    if not perfil["resumen_profesional"]:
        perfil["alertas"].append("Resumen profesional vacío — no había información suficiente.")

    if not perfil["experiencia_profesional"]:
        perfil["alertas"].append("No se encontraron bullets de experiencia profesional.")

    if not perfil["conocimientos_clave"]:
        perfil["alertas"].append("Sin conocimientos clave detectados en el CV.")

    if not perfil["idiomas"]:
        perfil["alertas"].append("Idiomas no declarados en el CV.")

    if not perfil["formacion_academica"]:
        perfil["alertas"].append("Formación académica no encontrada en el CV.")

    # Unificación: las certificaciones se incorporan a "formacion_academica"
    # (la plantilla las agrupa bajo el mismo bloque). Red de seguridad por si la
    # IA aún devuelve un campo "certificaciones" separado.
    certs_sueltas = _lista(datos.get("certificaciones", []))
    if certs_sueltas:
        perfil["formacion_academica"] = perfil["formacion_academica"] + certs_sueltas

    # Eliminar duplicados en listas para evitar redundancias visibles
    perfil["formacion_academica"] = _deduplicar(perfil["formacion_academica"])
    perfil["experiencia_profesional"] = _deduplicar(perfil["experiencia_profesional"])
    perfil["conocimientos_clave"] = _deduplicar(perfil["conocimientos_clave"])

    # Truncar resumen a 3 líneas (según requerimiento de ideal 3 líneas)
    perfil["resumen_profesional"] = _truncar_resumen(perfil["resumen_profesional"])

    return perfil


def _fit_score(valor):
    """
    Devuelve el fit_score como entero 0-100, o None si la IA no pudo calcularlo
    (por falta de contexto o evidencia). NUNCA fabrica un valor por defecto.
    """
    if valor is None or valor == "":
        return None
    try:
        score = int(float(valor))
    except (TypeError, ValueError):
        return None
    if score < 0 or score > 100:
        return None
    return score


def _str(valor) -> str:
    """Convierte a string o devuelve ''."""
    if valor is None:
        return ""
    if isinstance(valor, list):
        return ", ".join(str(v) for v in valor)
    return str(valor).strip()


def _lista(valor) -> list:
    """Convierte a lista limpia de strings."""
    if not valor:
        return []
    if isinstance(valor, str):
        # Si viene como texto separado por \n, convertir
        return [line.strip() for line in valor.split("\n") if line.strip()]
    if isinstance(valor, list):
        return [str(item).strip() for item in valor if str(item).strip()]
    return []


def _deduplicar(lista: list) -> list:
    """Elimina duplicados exactos manteniendo orden."""
    vistos = set()
    resultado = []
    for item in lista:
        if item.lower() not in vistos:
            vistos.add(item.lower())
            resultado.append(item)
    return resultado


def _truncar_resumen(resumen: str) -> str:
    """Si el resumen tiene más de 3 líneas lógicas, lo trunca."""
    if not resumen:
        return ""
    # Dividir por saltos de línea y tomar máximo 3
    lineas = [l.strip() for l in resumen.split("\n") if l.strip()]
    if len(lineas) > 3:
        return " ".join(lineas[:3])
    # Si es una sola línea muy larga (> 300 chars), no truncar — el PPT lo manejará
    return resumen
