"""
ai_service.py — Módulo LLM para extracción y redacción de perfiles Big4.
Multi-proveedor: OpenAI, Google Gemini o Anthropic Claude (elegible por el usuario).
Los SDK de cada proveedor se importan de forma perezosa (lazy) para no exigir tenerlos
todos instalados ni todas las API keys configuradas.

REGLAS ESTRICTAS:
- NO inventar experiencia, certificaciones, herramientas, idiomas ni logros.
- NO asumir seniority sin evidencia documental suficiente.
- NO rellenar vacíos para que "se vea mejor".
- Solo incluir lo que está explícitamente en el input.
"""

import os
import json
import time
from dotenv import load_dotenv
from config import (
    LLM_TEMPERATURE,
    SENIORITY_LEVELS,
    FORMATOS_EXPERIENCIA,
    FORMATO_EXPERIENCIA_DEFAULT,
    PROVEEDORES,
    PROVEEDOR_DEFAULT,
)

load_dotenv(override=True)


# Esquema estricto del perfil para Structured Outputs (response_format json_schema).
# Con strict=True el modelo NO puede generar una respuesta que viole esta estructura:
# se garantiza a nivel de generación que existan todos los campos y con el tipo correcto.
_PERFIL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "nombre", "rol_seniority", "enfoque_fit", "formacion_academica",
        "conocimientos_clave", "idiomas", "resumen_profesional",
        "experiencia_profesional", "fit_score", "semaforo", "alertas",
    ],
    "properties": {
        "nombre": {"type": "string"},
        "rol_seniority": {"type": "string"},
        "enfoque_fit": {"type": "string"},
        "formacion_academica": {"type": "array", "items": {"type": "string"}},
        "conocimientos_clave": {"type": "array", "items": {"type": "string"}},
        "idiomas": {"type": "string"},
        "resumen_profesional": {"type": "string"},
        "experiencia_profesional": {"type": "array", "items": {"type": "string"}},
        # fit_score puede ser null cuando no hay contexto/evidencia suficiente.
        "fit_score": {"type": ["integer", "null"]},
        "semaforo": {
            "type": "object",
            "additionalProperties": False,
            "required": ["cumple", "gaps"],
            "properties": {
                "cumple": {"type": "array", "items": {"type": "string"}},
                "gaps": {"type": "array", "items": {"type": "string"}},
            },
        },
        "alertas": {"type": "array", "items": {"type": "string"}},
    },
}


def extrae_perfil_cv(
    cv_text: str,
    contexto_proyecto: str = "",
    idioma: str = "es",
    formato: str = FORMATO_EXPERIENCIA_DEFAULT,
    proveedor: str = None,
) -> dict:
    """
    Extrae y estructura el perfil profesional desde el texto del CV.

    Args:
        cv_text: Texto plano extraído del CV.
        contexto_proyecto: RFP, descripción del rol o contexto adicional (opcional).
        idioma: Código de idioma de salida ("es" o "en"). Default "es".
        formato: Formato de redacción de la experiencia profesional:
            - "con_empresa": cada bullet inicia con el nombre de la empresa/cliente
              tal como aparece en el CV.
            - "sin_empresa": no se nombra la empresa; se describe la actividad y se
              referencia el tipo/sector de la empresa.
        proveedor: Motor de IA a usar ("openai", "gemini" o "anthropic"). Si es None
            o inválido, se usa PROVEEDOR_DEFAULT.

    Returns:
        dict con el perfil estructurado según el JSON intermedio estándar.
    """

    seniority_lista = ", ".join(f'"{s}"' for s in SENIORITY_LEVELS)

    if formato not in FORMATOS_EXPERIENCIA:
        formato = FORMATO_EXPERIENCIA_DEFAULT

    if formato == "sin_empresa":
        instruccion_formato = (
            "FORMATO DE EXPERIENCIA — SIN EMPRESA (ANONIMIZADO):\n"
            "En cada bullet de 'experiencia_profesional' NO menciones el nombre propio de ninguna "
            "empresa o cliente. Describe directamente la actividad realizada y, cuando el CV lo permita, "
            "haz referencia al TIPO o SECTOR de la organización (ej: 'para una entidad del sector bancario', "
            "'en una compañía de retail', 'para un organismo público'). El sector debe derivarse de "
            "información presente en el CV; si no es posible determinarlo con la información disponible, "
            "omite la referencia al tipo de empresa en lugar de inventarla. NUNCA incluyas el nombre real "
            "de la empresa ni datos que permitan identificarla directamente."
        )
    else:
        instruccion_formato = (
            "FORMATO DE EXPERIENCIA — CON EMPRESA:\n"
            "Cuando una experiencia tenga una empresa o cliente identificable en el CV, antepón su nombre "
            "(tal como aparece en el CV) al describir la actividad. Si no hay empresa identificable, describe "
            "solo la actividad. NUNCA inventes el nombre de una empresa."
        )

    instruccion_negrita = (
        "RESALTADO EN NEGRITA: En 'resumen_profesional' y en cada bullet de 'experiencia_profesional', "
        "marca las ideas MÁS IMPORTANTES (logros clave, herramientas críticas, resultados, "
        "responsabilidades de alto impacto) envolviéndolas entre dobles asteriscos en formato Markdown: "
        "**texto importante**. El resaltado SOLO enfatiza texto que ya existe; NO agrega información nueva. "
        "Resalta únicamente lo esencial (1 a 3 fragmentos breves por bullet), nunca frases completas ni el "
        "bullet entero. No uses asteriscos en ningún otro campo del JSON."
    )

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

IDIOMA DE SALIDA:
{instruccion_idioma}

{instruccion_formato}

{instruccion_negrita}

REGLAS ABSOLUTAS — INCUMPLIRLAS ES UN ERROR GRAVE:
1. NO inventes experiencia, certificaciones, herramientas ni idiomas.
2. NUNCA uses la frase "Por validar". Si falta información, déjalo como cadena vacía "" o lista vacía [].
3. NO inferir métricas, números de proyectos, años de experiencia ni impacto cuantitativo no declarado.
4. "nombre": Usa el nombre tal como aparece en el CV. Si la persona tiene múltiples nombres y/o apellidos, conserva el primer nombre + primer apellido, pero NUNCA inventes, traduzcas ni alteres el nombre. El nombre suele estar en el encabezado más prominente. En formatos de "Ficha de Perfil" o columnas, busca en la parte superior izquierda o central. Si no se encuentra ningún nombre, deja "" y añade una alerta.
5. "rol_seniority": Pon un rol y usa estrictamente la estructura de seniority de Minsait: Analyst, Consultant, Senior Consultant, Manager, Senior Manager, o Director (Ej: "Consultant | Gestión Financiera"). El seniority debe basarse en EVIDENCIA documental (años de experiencia, títulos previos, alcance de los roles desempeñados). Si el CV no aporta evidencia suficiente para inferir el seniority, deja "rol_seniority" como "" y añade una alerta. NUNCA asignes un seniority por defecto ni por suposición.
   - TRATAMIENTO DE FECHAS: NO consideres inválidas, "futuras" ni inconsistentes las fechas por ser recientes o posteriores a tu fecha de conocimiento; la fecha actual puede ser posterior a la que asumes. Las fechas recientes (2024, 2025, 2026 y posteriores) son VÁLIDAS y NO son motivo para abstenerse de asignar seniority ni de calcular fit_score. Usa las fechas del CV tal cual para estimar años de experiencia. Solo marca "inconsistencia" si existe una contradicción interna REAL (p. ej., una fecha de fin anterior a su propia fecha de inicio).
6. "resumen_profesional": Genera un resumen ejecutivo en UNA sola línea/párrafo continuo, SIN saltos de línea (no uses '\n' ni '\\n' dentro del texto), con un MÁXIMO ESTRICTO de 45 palabras. VALIDACIÓN: antes de responder, cuenta las palabras del resumen; si supera 45, condénsalo hasta cumplir. Nunca entregues más de 45 palabras.
7. "conocimientos_clave": Extrae herramientas, metodologías y frameworks. Máximo 6 bullets. Consolida herramientas similares usando comas.
8. "experiencia_profesional": Lista TODAS las responsabilidades, funciones y logros que aparezcan en el CV. Redacta cada bullet de forma CONCISA: UNA sola idea o actividad por bullet, en 1 frase breve (orientativamente 12 a 22 palabras) con wording ejecutivo. EVITA párrafos largos y bullets que encadenen varias acciones. ATENCIÓN: esta ampliación es SOLO de redacción; está terminantemente PROHIBIDO añadir herramientas, cifras, porcentajes, clientes, sectores, tecnologías, resultados o responsabilidades que NO estén en el CV. No crees actividades nuevas para rellenar espacio. NO hay número mínimo de bullets: si el CV es escueto, devuelve solo los que correspondan (es preferible pocos bullets bien redactados a inventar) y añade una alerta indicando que la experiencia documentada es limitada.
   - GRANULARIDAD: Cada actividad, logro o responsabilidad DISTINTA del CV va en su PROPIO bullet corto. Si un punto del CV encadena varias acciones, SEPÁRALO en varios bullets (uno por acción) en lugar de un bullet largo. Prefiere MUCHOS bullets breves a pocos bullets extensos. Cuando el CV tenga material abundante, aprovecha el presupuesto generando MÁS bullets (no alargándolos), siempre con información real del CV. Esto NO es licencia para inventar, inflar ni añadir detalles no declarados: si el CV tiene poco material, devuelve pocos bullets sin forzar.
   - LÍMITE DE EXTENSIÓN (ESTRICTO E INVIOLABLE): la suma total de palabras de TODOS los bullets de "experiencia_profesional" NO debe superar las 350 palabras. VALIDACIÓN OBLIGATORIA: antes de entregar el JSON, CUENTA el total de palabras sumando todos los bullets; si el total supera 350, DEBES recortar o condensar hasta quedar en 350 o menos, y recién entonces responder. Bajo ninguna circunstancia entregues más de 350 palabras. Si el contenido declarado en el CV excede ese límite: (a) si se entregó "contexto_proyecto", prioriza y conserva las experiencias y actividades MÁS relevantes para ese rol/descripción, condensando o resumiendo las menos relevantes; (b) si NO hay contexto, sintetiza y resume consolidando actividades similares. NUNCA recortes de forma que se pierda información esencial: prefiere condensar la redacción antes que eliminar logros o responsabilidades importantes. Si tuviste que resumir por exceder el límite, añade una alerta indicándolo.
   - MANEJO DE FORMATO: En perfiles resumen con columnas, identifica el bloque de experiencia y desglosa las actividades realmente declaradas; reorganizar y reformular es válido, fabricar contenido nuevo NO lo es.
   - ESTILO DE REDACCIÓN: Aplica el "FORMATO DE EXPERIENCIA" y el "RESALTADO EN NEGRITA" indicados arriba a cada bullet.
9. CERTIFICACIONES: NO generes un campo "certificaciones" separado. Incorpora las certificaciones relevantes DENTRO de "formacion_academica" (ver punto 10), ya que la plantilla las agrupa bajo el mismo bloque.
10. "formacion_academica": Extrae la formación académica Y las certificaciones relevantes en este MISMO campo (máximo 6 bullets combinados; coloca las certificaciones después de los estudios). NUNCA incluyas el año de graduación o periodos. REGLA DE SIGLAS: Si la universidad está en la siguiente lista, usa SIEMPRE sus siglas. Si la universidad NO está en la lista, mantén su nombre completo tal como aparece en el CV — NUNCA inventes siglas:
    - Pontificia Universidad Católica del Perú -> PUCP
    - Universidad del Pacífico -> UP
    - Universidad de Piura -> UP
    - Universidad Peruana de Ciencias Aplicadas -> UPC
    - Universidad de Lima -> UL
    - Universidad Cayetano Heredia -> UCH
    - Business School / Escuela de Negocios -> BS
11. "conocimientos_clave": Extrae máximo 6 bullets. REGLA DE ESPACIO: Resta 1 al límite total de bullets por cada línea adicional (double line) que se genere.
12. "idiomas": NUNCA dejes este campo vacío. Si el CV está redactado en español, incluye SIEMPRE "Español" (junto con los demás idiomas que el CV declare explícitamente). Si el CV no especifica ningún idioma, pon el idioma en que está redactado el CV.
13. "fit_score": DEBES calcularlo siguiendo esta FÓRMULA MATEMÁTICA ESTRICTA (0 a 100):
    - 40% HERRAMIENTAS: Pondera la cantidad total y relevancia de herramientas del stack técnico (Ej: SQL, Python, Cloud). Premia la variedad técnica.
    - 30% FUNCIONES: Alineación con las responsabilidades del contexto. Premia la profundidad de logros.
    - 20% SENIORITY/TRAYECTORIA: Años totales de experiencia. Analyst (0-3y), Consultant (3-5y), Senior Consultant (5-8y), Manager (8y+). Entrega mayor puntaje si posee más años comprobados.
    - 10% SECTOR: Experiencia específica en la industria del cliente.
    - REGLA DE IDIOMA: USA SIEMPRE términos en inglés para seniority: Analyst, Consultant, Senior Consultant, Manager. NUNCA uses Consultor, Gerente, Analista o similares.
    - PROHIBICIÓN: No uses números redondos genéricos (ej: 85%). El score debe derivarse de la evidencia del CV y del contexto.
    - SIN CONTEXTO O SIN EVIDENCIA: Si no se entregó "contexto_proyecto", o si falta información en el CV para evaluar alguno de los 4 ejes, devuelve "fit_score": null y añade una alerta explicando el motivo. NO fabriques un número que aparente precisión que no tienes.
14. "enfoque_fit": Una frase de 5-10 palabras que resuma el ajuste real o gap crítico. Si no se entregó "contexto_proyecto", devuelve "" y añade una alerta — NO opines sobre el ajuste sin un rol objetivo. NUNCA envíes "Resumen de perfil".
15. "semaforo": Objeto con "cumple" y "gaps", evaluados SOLO contra el "contexto_proyecto". Si no se entregó contexto, devuelve "cumple": [], "gaps": [] y añade la alerta "Semáforo no calculable sin contexto del rol". NUNCA inventes gaps ni fortalezas sin un rol objetivo de referencia.
16. LAYOUT: Segmentado por secciones (ENCABEZADO, LATERAL, PRINCIPAL).

ESTRUCTURA JSON: La estructura del JSON de salida está definida y forzada por el esquema
(Structured Outputs), por lo que NO necesitas memorizar su forma: limítate a rellenar cada
campo respetando las reglas anteriores. Recordatorios de contenido:
- "resumen_profesional": UNA sola línea continua, sin saltos de línea, máximo 45 palabras.
- El resaltado **negrita** SOLO en "resumen_profesional" y "experiencia_profesional"; ningún
  otro campo lleva asteriscos.
- "fit_score" entero 0-100 o null; "semaforo" con listas "cumple" y "gaps".
- "experiencia_profesional": bullets CORTOS y concisos (1 idea por bullet, ~12-22 palabras); muchos bullets breves mejor que pocos largos. Máximo 350 palabras en total (prioriza por relevancia al contexto o sintetiza si excede).
- No incluyas un campo "certificaciones": va dentro de "formacion_academica"."""

    contexto_bloque = f"\n\nCONTEXTO DEL PROYECTO O ROL (prioriza experiencia relevante sin inventar):\n{contexto_proyecto}" if contexto_proyecto.strip() else ""
    user_prompt = f"CV PARA PROCESAR:{contexto_bloque}\n\n{cv_text}"

    # ── Resolver proveedor y API key ─────────────────────────────────────────────
    proveedor = (proveedor or PROVEEDOR_DEFAULT).lower()
    if proveedor not in PROVEEDORES:
        proveedor = PROVEEDOR_DEFAULT
    cfg = PROVEEDORES[proveedor]
    api_key = os.getenv(cfg["env"])
    if not api_key:
        return _perfil_vacio_con_error(
            f"Falta la API key del proveedor '{cfg['label']}'. Configura {cfg['env']} en backend/.env."
        )

    # ── Dispatch al proveedor elegido (con reintentos ante errores transitorios) ──
    intentos = 3
    for intento in range(1, intentos + 1):
        try:
            if proveedor == "openai":
                return _extraer_openai(system_prompt, user_prompt, cfg["model"], api_key)
            elif proveedor == "gemini":
                return _extraer_gemini(system_prompt, user_prompt, cfg["model"], api_key)
            elif proveedor == "anthropic":
                return _extraer_anthropic(system_prompt, user_prompt, cfg["model"], api_key)
            else:
                return _perfil_vacio_con_error(f"Proveedor no soportado: {proveedor}")

        except json.JSONDecodeError as e:
            print(f"[ai_service] Error parseando JSON de {proveedor}: {e}")
            return _perfil_vacio_con_error("Respuesta de IA no fue JSON válido.")
        except ModuleNotFoundError as e:
            print(f"[ai_service] SDK no instalado para {proveedor}: {e}")
            return _perfil_vacio_con_error(
                f"El SDK del proveedor '{cfg['label']}' no está instalado ({e.name}). "
                f"Instálalo con pip (ver requirements.txt)."
            )
        except Exception as e:
            # Errores transitorios del proveedor (saturación, rate limit): reintentar.
            if intento < intentos and _es_error_transitorio(e):
                espera = 2 * intento
                print(f"[ai_service] Error transitorio de {proveedor} "
                      f"(intento {intento}/{intentos}); reintentando en {espera}s...")
                time.sleep(espera)
                continue
            print(f"[ai_service] Error llamando a {proveedor}: {e}")
            return _perfil_vacio_con_error(str(e))


# ── Implementaciones por proveedor ───────────────────────────────────────────────

def _extraer_openai(system_prompt: str, user_prompt: str, model: str, api_key: str) -> dict:
    """OpenAI con Structured Outputs (json_schema strict)."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    base_kwargs = dict(
        model=model,
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "perfil_cv", "strict": True, "schema": _PERFIL_SCHEMA},
        },
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    try:
        response = client.chat.completions.create(temperature=LLM_TEMPERATURE, **base_kwargs)
    except Exception as e_temp:
        # Algunos modelos con razonamiento (familia GPT-5) solo aceptan la temperatura por defecto.
        if "temperature" in str(e_temp).lower():
            print("[ai_service] El modelo no acepta 'temperature'; reintentando sin ese parámetro.")
            response = client.chat.completions.create(**base_kwargs)
        else:
            raise

    msg = response.choices[0].message
    if getattr(msg, "refusal", None):
        raise RuntimeError(f"El modelo rechazó la solicitud: {msg.refusal}")
    return json.loads((msg.content or "").strip())


def _extraer_anthropic(system_prompt: str, user_prompt: str, model: str, api_key: str) -> dict:
    """Anthropic Claude con tool-use forzado (el input_schema fuerza la estructura)."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    tool = {
        "name": "registrar_perfil",
        "description": "Registra el perfil del CV estructurado según el esquema indicado.",
        "input_schema": _PERFIL_SCHEMA,
    }
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=LLM_TEMPERATURE,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[tool],
        tool_choice={"type": "tool", "name": "registrar_perfil"},
    )
    for block in response.content:
        if getattr(block, "type", None) == "tool_use":
            return dict(block.input)
    raise RuntimeError("Claude no devolvió la herramienta con el perfil estructurado.")


def _extraer_gemini(system_prompt: str, user_prompt: str, model: str, api_key: str) -> dict:
    """Google Gemini con salida JSON (response_json_schema si el SDK lo soporta)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    base = dict(
        system_instruction=system_prompt,
        temperature=LLM_TEMPERATURE,
        response_mime_type="application/json",
    )
    # Intentamos con esquema JSON estricto; si esta versión del SDK no lo acepta,
    # caemos a JSON sin esquema (el prompt + el normalizer cubren la estructura).
    try:
        config = types.GenerateContentConfig(response_json_schema=_PERFIL_SCHEMA, **base)
    except Exception:
        config = types.GenerateContentConfig(**base)

    response = client.models.generate_content(model=model, contents=user_prompt, config=config)
    return json.loads((response.text or "").strip())


def _es_error_transitorio(e) -> bool:
    """Detecta errores temporales del proveedor (saturación, rate limit, timeouts)
    que conviene reintentar, en lugar de fallar de inmediato."""
    s = str(e).lower()
    señales = (
        "503", "429", "500", "502", "529",
        "unavailable", "overloaded", "high demand", "rate limit",
        "timeout", "temporarily", "try again",
    )
    return any(x in s for x in señales)


def _perfil_vacio_con_error(motivo: str) -> dict:
    """Devuelve estructura vacía con alerta cuando falla la IA."""
    return {
        "nombre": "",
        "rol_seniority": "",
        "formacion_academica": [],
        "conocimientos_clave": [],
        "idiomas": "",
        "resumen_profesional": "",
        "experiencia_profesional": [],
        "fit_score": None,
        "semaforo": {"cumple": [], "gaps": []},
        "alertas": [f"Error en extracción IA: {motivo}"],
    }
