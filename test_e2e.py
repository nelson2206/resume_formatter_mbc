"""
Test end-to-end: extrae perfil de la plantilla de ejemplo y genera un PPT de prueba.
"""
import sys, os
# Asegura que los módulos del backend estén disponibles
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Directorio raíz del proyecto

from ppt_builder import generar_ppt_desde_plantilla
from normalizer import normalizar_perfil

# Perfil de prueba — simula lo que devolvería la IA
datos_raw = {
    "nombre": "Carlos Mendoza Ríos",
    "rol_seniority": "Senior Consultant | Transformación Digital",
    "formacion_academica": "Ingeniería Industrial — Universidad Nacional (2016)",
    "conocimientos_clave": [
        "SAP FI/CO",
        "Power BI y Power Automate",
        "Gestión de proyectos (PMI)",
        "Python y SQL",
        "Mejora de procesos operativos",
    ],
    "idiomas": "Español Nativo | Inglés B2 (TOEFL 94)",
    "resumen_profesional": "Consultor con trayectoria en proyectos de transformación digital e implementación ERP en sectores financiero e industrial.",
    "experiencia_profesional": [
        "Lideró implementación SAP FI/CO para cliente del sector bancario, coordinando equipo de 6 consultores.",
        "Desarrolló dashboards ejecutivos en Power BI para monitoreo de indicadores de riesgo operativo.",
        "Automatizó procesos de reporte usando Power Automate, reduciendo tiempo manual de reporteo.",
        "Coordinó con áreas de auditoría interna para asegurar cumplimiento regulatorio en proyectos ERP.",
        "Participó en levantamiento de requerimientos y diseño funcional de módulos financieros en SAP.",
    ],
    "alertas": [],
}

perfil = normalizar_perfil(datos_raw)
print("Perfil normalizado:")
for k, v in perfil.items():
    print(f"  {k}: {v}")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
template = os.path.join(PROJECT_ROOT, "templates", "CV template.pptx")
output = os.path.join(PROJECT_ROOT, "outputs", "TEST_Carlos_Mendoza.pptx")
os.makedirs("outputs", exist_ok=True)

generar_ppt_desde_plantilla(template, output, perfil)
print(f"\n✅ PPT generado: {output}")
print("   Ábrelo en PowerPoint para verificar el diseño.")
