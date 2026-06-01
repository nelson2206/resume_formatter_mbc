import React from 'react';
import { X, User, Briefcase, GraduationCap, Globe, Cpu } from 'lucide-react';

// Convierte marcadores Markdown **negrita** en elementos <strong>.
// Devuelve un array de nodos React listos para renderizar.
const renderNegrita = (texto) => {
  if (!texto) return texto;
  const partes = String(texto).split(/\*\*(.+?)\*\*/g);
  return partes.map((parte, i) =>
    i % 2 === 1
      ? <strong key={i}>{parte}</strong>
      : <React.Fragment key={i}>{parte.replace(/\*\*/g, '')}</React.Fragment>
  );
};

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
            
            {/* Cabecera Corporativa Minsait */}
            <header className="slide-header">
              <div className="header-name">
                <h2>{perfil.nombre || "Nombre del Consultor"}</h2>
              </div>
              <div className="header-rol">
                <h3>{perfil.rol_seniority || "Role / Seniority"}</h3>
              </div>
            </header>

            <div className="slide-body">
              {/* Columna Lateral (Izquierda) */}
              <aside className="slide-sidebar">
                
                <section className="slide-sidebar-section">
                  <div className="section-title-row">
                    <GraduationCap size={14} className="icon-minsait" />
                    <h4>FORMACIÓN ACADÉMICA</h4>
                  </div>
                  <ul>
                    {perfil.formacion_academica?.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                </section>

                <section className="slide-sidebar-section">
                  <div className="section-title-row">
                    <Globe size={14} className="icon-minsait" />
                    <h4>IDIOMAS</h4>
                  </div>
                  <p className="sidebar-text">{perfil.idiomas}</p>
                </section>

                <section className="slide-sidebar-section highlight">
                  <div className="section-title-row">
                    <Cpu size={14} className="icon-minsait" />
                    <h4>CONOCIMIENTOS CLAVE</h4>
                  </div>
                  <ul className="knowledge-list">
                    {perfil.conocimientos_clave?.map((k, i) => <li key={i}>{k}</li>)}
                  </ul>
                </section>
              </aside>

              {/* Área Principal (Derecha) */}
              <main className="slide-main">
                
                <section className="slide-main-section">
                  <div className="section-title-row">
                    <User size={14} className="icon-minsait" />
                    <h4>RESUMEN PROFESIONAL</h4>
                  </div>
                  <div className="resumen-content">
                    {perfil.resumen_profesional?.split('\n').map((line, i) => (
                      <p key={i}>{renderNegrita(line)}</p>
                    ))}
                  </div>
                </section>

                <section className="slide-main-section flex-grow">
                  <div className="section-title-row">
                    <Briefcase size={14} className="icon-minsait" />
                    <h4>RESPONSABILIDADES Y LOGROS</h4>
                  </div>
                  <ul className="experience-list">
                    {perfil.experiencia_profesional?.map((exp, i) => (
                      <li key={i}>{renderNegrita(exp)}</li>
                    ))}
                  </ul>
                </section>

              </main>
            </div>

            {/* Footer de diapositiva */}
            <footer className="slide-footer">
              <span>Minsait - An Indra Company</span>
              <span className="footer-page">1</span>
            </footer>

          </div>
        </div>
      </div>
    </div>
  );
};

export default SlidePreview;
