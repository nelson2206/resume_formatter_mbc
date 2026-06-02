import React from 'react';
import { X } from 'lucide-react';

// Convierte marcadores Markdown **negrita** en elementos <strong>,
// igual que el resaltado en negrita del PPTX descargable.
const renderNegrita = (texto) => {
  if (!texto) return texto;
  const partes = String(texto).split(/\*\*(.+?)\*\*/g);
  return partes.map((parte, i) =>
    i % 2 === 1
      ? <strong key={i}>{parte}</strong>
      : <React.Fragment key={i}>{parte.replace(/\*\*/g, '')}</React.Fragment>
  );
};

// Réplica fiel de la plantilla PPTX (CV template.pptx):
//  - Columna izquierda: cabecera plum (nombre/rol) + Formación académica,
//    Conocimientos Clave, Idiomas (en ese orden).
//  - Columna derecha: "Experiencia profesional" -> resumen (párrafo líder) -> bullets.
const SlidePreview = ({ perfil, onClose }) => {
  if (!perfil) return null;

  return (
    <div className="preview-overlay">
      <div className="preview-modal">
        {/* Barra de control superior */}
        <div className="preview-controls">
          <span className="preview-tag">VISTA PREVIA DE DIAPOSITIVA</span>
          <button className="preview-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* El "Slide" (Simulación de diapositiva 16:9) */}
        <div className="slide-container">
          <div className="slide-mockup">
            <div className="slide-body">

              {/* Columna izquierda: cabecera + secciones del lateral */}
              <aside className="slide-sidebar">
                <header className="slide-header">
                  <span className="header-label">CV PERFILES EQUIPO DE TRABAJO</span>
                  <h2 className="header-name">{perfil.nombre || "Nombre del Consultor"}</h2>
                  <h3 className="header-rol">{perfil.rol_seniority || "Role | Seniority"}</h3>
                </header>

                <section className="slide-sidebar-section">
                  <h4>Formación académica</h4>
                  <ul>
                    {perfil.formacion_academica?.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                </section>

                <section className="slide-sidebar-section">
                  <h4>Conocimientos Clave</h4>
                  <ul>
                    {perfil.conocimientos_clave?.map((k, i) => <li key={i}>{k}</li>)}
                  </ul>
                </section>

                <section className="slide-sidebar-section">
                  <h4>Idiomas</h4>
                  <p className="sidebar-text">{perfil.idiomas}</p>
                </section>
              </aside>

              {/* Columna derecha: Experiencia profesional */}
              <main className="slide-main">
                <h4 className="main-title">Experiencia profesional</h4>
                <div className="resumen-content">
                  {perfil.resumen_profesional?.split('\n').map((line, i) => (
                    <p key={i}>{renderNegrita(line)}</p>
                  ))}
                </div>
                <ul className="experience-list">
                  {perfil.experiencia_profesional?.map((exp, i) => (
                    <li key={i}>{renderNegrita(exp)}</li>
                  ))}
                </ul>
              </main>

            </div>

            {/* Footer de diapositiva (número de página) */}
            <footer className="slide-footer">
              <span className="footer-page">1</span>
            </footer>

          </div>
        </div>
      </div>
    </div>
  );
};

export default SlidePreview;
