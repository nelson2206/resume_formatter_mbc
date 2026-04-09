"""
ai_service.py — Módulo LLM para extracción y redacción de perfiles Big4.
Usa OpenAI GPT. Desacoplado para facilitar cambio de proveedor.

REGLAS ESTRICTAS:
- NO inventar experiencia, certificaciones, herramientas, idiomas ni logros.
- NO asumir seniority sin evidencia documental suficiente.
- NO rellenar vacíos para que "se vea mejor".
- Solo incluir lo que está explícitamente en el input.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from config import LLM_MODEL, LLM_TEMPERATURE, SENIORITY_LEVELS

load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def extrae_perfil_cv(cv_text: str, contexto_proyecto: str = "", idioma: str = "es") -> dict:
    """
    Extrae y estructura el perfil profesional desde el texto del CV.
    
    Args:
        cv_text: Texto plano extraído del CV.
        contexto_proyecto: RFP, descripción del rol o contexto adicional (opcional).
        idioma: Código de idioma de salida ("es" o "en"). Default "es".
        
    Returns:
        dict con el perfil estructurado según el JSON intermedio estándar.
    """
    
    seniority_lista = ", ".join(f'"{s}"' for s in SENIORITY_LEVELS)
    
    if idioma == "en":
        instruccion_idioma = (
            "Write the redacted content (resumen_profesional and experiencia_profesional bullets) in English. "
            "IMPORTANT: Do NOT translate proper nouns: names of people, companies, universities, certifications, "
            "tools, technologies, or institutions. These must remain exactly as they appear in the source."
        )
    else:
        instruccion_idioma = (
            "Escribe el contenido redactado (resumen_profesional y bullets de experiencia_profesional) en español. "
            "IMPORTANTE: No traduzcas nombres propios: nombres de personas, empresas, universidades, certificaciones, "
            "herramientas, tecnologías ni instituciones. Estos deben quedar exactamente como aparecen en la fuente."
        )

    system_prompt = f"""Eres un agente experto en staffing de consultoría de Minsait.
Tu objetivo es extraer datos de un CV y estructurarlos en un JSON estricto.

REGLAS ABSOLUTAS — INCUMPLIRLAS ES UN ERROR GRAVE:
1. NO inventes experiencia, certificaciones, herramientas ni idiomas.
2. NUNCA uses la frase "Por validar". Si falta información, déjalo como cadena vacía "" o lista vacía [].
3. NO inferir métricas, números de proyectos, años de experiencia ni impacto cuantitativo no declarado.
4. "nombre": Debes colocar exactamente 1 nombre y 1 apellido. El nombre suele estar en el encabezado más prominente. En formatos de "Ficha de Perfil" o columnas, busca en la parte superior izquierda o central.
5. "rol_seniority": Pon un rol y usa estrictamente la estructura de seniority de Minsait: Analyst, Consultant, Senior Consultant, Manager, Senior Manager, o Director (Ej: "Consultant | Gestión Financiera").
6. "resumen_profesional": Genera un resumen ejecutivo de entre 2 y 3 líneas (ideal 3 líneas).
7. "conocimientos_clave": Extrae herramientas, metodologías y frameworks. Máximo 6 bullets. Consolida herramientas similares usando comas.
8. "experiencia_profesional": Debe tener un detalle profundo. Mínimo 250 palabras en total. Idealmente busca alcanzar hasta 20 bullets detallados si la información lo permite, sin inventar hechos. Como MÍNIMO ABSOLUTO debe poseer 12 bullets.
   - MANEJO DE FORMATO: En perfiles resumen con columnas, identifica el bloque de experiencia y desglosa minuciosamente las actividades para acercarte al ideal de 20 bullets con wording ejecutivo.
9. "certificaciones": Extrae máximo 5 bullets. Límite de extensión: máximo 24 palabras en total.
10. "formacion_academica": Extrae máximo 5 bullets. NUNCA incluyas el año de graduación o periodos. REGLA DE SIGLAS OBLIGATORIA: Nunca uses el nombre completo de la universidad, usa SIEMPRE sus siglas:
    - Pontificia Universidad Católica del Perú -> PUCP
    - Universidad del Pacífico -> UP
    - Universidad de Piura -> UP
    - Universidad Peruana de Ciencias Aplicadas -> UPC
    - Universidad de Lima -> UL
    - Universidad Cayetano Heredia -> UCH
    - Business School / Escuela de Negocios -> BS
11. "conocimientos_clave": Extrae máximo 6 bullets. REGLA DE ESPACIO: Resta 1 al límite total de bullets por cada línea adicional (double line) que se genere.
12. "idiomas": NUNCA dejes este campo vacío. Si el CV no especifica, pon el idioma original del CV (Ej: "Español").
13. "fit_score": DEBES calcularlo siguiendo esta FÓRMULA MATEMÁTICA ESTRICTA (0 a 100):
    - 40% HERRAMIENTAS: Pondera la cantidad total y relevancia de herramientas del stack técnico (Ej: SQL, Python, Cloud). Premia la variedad técnica.
    - 30% FUNCIONES: Alineación con las responsabilidades del contexto. Premia la profundidad de logros.
    - 20% SENIORITY/TRAYECTORIA: Años totales de experiencia. Analyst (0-3y), Consultant (3-5y), Senior Consultant (5-8y), Manager (8y+). Entrega mayor puntaje si posee más años comprobados.
    - 10% SECTOR: Experiencia específica en la industria del cliente.
    - REGLA DE IDIOMA: USA SIEMPRE términos en inglés para seniority: Analyst, Consultant, Senior Consultant, Manager. NUNCA uses Consultor, Gerente, Analista o similares.
    - PROHIBICIÓN: No uses números redondos genéricos (ej: 85%). Busca precisión matemática basada en evidencia (ej: 74, 88, 62).
14. "enfoque_fit": CAMPO OBLIGATORIO. Una frase de 5-10 palabras que resuma el ajuste real o gap crítico. NUNCA envíes "Resumen de perfil".
15. "semaforo": Objeto con "cumple" (3-4 puntos) y "gaps" (2-3 puntos).
16. LAYOUT: Segmentado por secciones (ENCABEZADO, LATERAL, PRINCIPAL).

Salida JSON:
{{
    "nombre": "Nombre y 1 Apellido",
    "rol_seniority": "Role | Consultant",
    "enfoque_fit": "Resumen crítico del ajuste.",
    ...
}}

ESTRUCTURA JSON OBLIGATORIA (devuelve SOLO el JSON, sin texto adicional):
{{{{
    "nombre": "Nombre y 1 Apellido",
    "rol_seniority": "Role | Seniority (Analyst, Consultant, Senior Consultant or Manager)",
    "enfoque_fit": "Frase corta estratégica (5-10 palabras).",
    "formacion_academica": ["Formación 1, Univ", "Formación 2, Univ"],
    "conocimientos_clave": ["Herramienta 1", "Metodología 2"],
    "idiomas": "Español",
    "certificaciones": ["Cert 1"],
    "resumen_profesional": "Línea 1.\\nLínea 2.\\nLínea 3.",
    "experiencia_profesional": ["Resp 1.", "Resp 2."],
    "fit_score": 78,
    "semaforo": {{{{
        "cumple": ["Punto 1", "Punto 2"],
        "gaps": ["Punto 3"]
    }}}},
    "alertas": []
}}}}"""

    contexto_bloque = f"\n\nCONTEXTO DEL PROYECTO O ROL (prioriza experiencia relevante sin inventar):\n{contexto_proyecto}" if contexto_proyecto.strip() else ""
    user_prompt = f"CV PARA PROCESAR:{contexto_bloque}\n\n{cv_text}"

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=LLM_TEMPERATURE,
        )
        text = response.choices[0].message.content.strip()
        data = json.loads(text)
        return data

    except json.JSONDecodeError as e:
        print(f"[ai_service] Error parseando JSON de OpenAI: {e}")
        return _perfil_vacio_con_error("Respuesta de IA no fue JSON válido.")
    except Exception as e:
        print(f"[ai_service] Error llamando a OpenAI: {e}")
        return _perfil_vacio_con_error(str(e))


def _perfil_vacio_con_error(motivo: str) -> dict:
    """Devuelve estructura vacía con alerta cuando falla la IA."""
    return {
        "nombre": "",
        "rol_seniority": "",
        "formacion_academica": [],
        "conocimientos_clave": [],
        "idiomas": "",
        "certificaciones": [],
        "resumen_profesional": "",
        "experiencia_profesional": [],
        "alertas": [f"Error en extracción IA: {motivo}"],
    }
