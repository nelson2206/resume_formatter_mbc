# Staffing AI Builder v2 🚀

Transforma CVs profesionales en presentaciones PowerPoint ejecutivas con el estándar visual de Minsait.

## Características
- **Extracción Inteligente**: Basada en OpenAI GPT para identificar roles, herramientas y logros.
- **Scoring de Ajuste (Fit Score)**: Evaluación algorítmica (40% Herramientas, 30% Funciones, 20% Seniority, 10% Sector).
- **Previsualización en Vivo**: Visor HTML que replica el slide corporativo antes de la descarga.
- **Leyenda Metodológica**: Barra de distribución proporcional para explicar el ajuste al cliente.
- **Diseño Minsait**: Estética premium integrada (Colores Plum/Fucsia).

## Instalación Local

### Requisitos
- Python 3.11+
- Node.js & npm

### Pasos
1. **Configurar Variables de Entorno**:
   Crea un archivo `.env` en la carpeta `backend/` con tu llave:
   ```env
   OPENAI_API_KEY=tu_sk_aquí
   ```
2. **Ejecutar**:
   Simplemente haz doble clic en `Lanzador.bat` (Windows).

## Despliegue en la Nube
Para que otros lo usen por link:
1. Sube este código a un repositorio de **GitHub**.
2. Conéctalo a servicios como **Render.com** o **Railway.app**.
3. Configura `OPENAI_API_KEY` en el panel de variables de entorno de la nube.

---
*Creado por Nelson Bernal C. para la optimización de procesos de Staffing AI.*
