import React, { useState, useRef, useCallback } from 'react';
import axios from 'axios';
import logo from './assets/logo.png';
import {
  UploadCloud, FileText, CheckCircle, XCircle, AlertTriangle,
  Download, Loader, ChevronDown, ChevronUp, Globe, Info, Eye, Briefcase
} from 'lucide-react';
import './index.css';
import SlidePreview from './components/SlidePreview';
import ScoringLegend from './components/ScoringLegend';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Helpers ────────────────────────────────────────────────────────────────────
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

const StatusBadge = ({ estado }) => {
  if (estado === 'ok') return (
    <span className="badge badge-ok"><CheckCircle size={12} /> Generado</span>
  );
  if (estado === 'error') return (
    <span className="badge badge-error"><XCircle size={12} /> Error</span>
  );
  if (estado === 'procesando') return (
    <span className="badge badge-processing"><Loader size={12} className="spin" /> Procesando</span>
  );
  return <span className="badge badge-pending">Pendiente</span>;
};

// ── Componente de fila de resultado ───────────────────────────────────────────
const ResultRow = ({ r, onDownload, onPreview }) => {
  const [expanded, setExpanded] = useState(false);
  const hasAlertas = r.alertas && r.alertas.length > 0;

  return (
    <div className={`result-row ${r.estado}`}>
      <div className="result-row-main">
        <div className="result-info">
          <FileText size={16} className="file-icon" />
          <div>
            <p className="result-filename">{r.archivo}</p>
            {r.nombre && <p className="result-meta">{r.nombre} · {r.rol_seniority}</p>}
            {r.error && <p className="result-error-msg">{r.error}</p>}
          </div>
        </div>
        <div className="result-actions">
          <StatusBadge estado={r.estado} />
          {(r.perfil || r.cv_id) && (
            <button className="btn-expand" onClick={() => onPreview(r)} title="Previsualizar Perfil">
              <Eye size={14} />
            </button>
          )}
          {r.ppt_id && (
            <button className="btn-download" onClick={() => onDownload(r.ppt_id)}>
              <Download size={14} /> Descargar
            </button>
          )}
          {hasAlertas && (
            <button className="btn-expand" onClick={() => setExpanded(!expanded)}>
              <AlertTriangle size={14} />
              {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          )}
        </div>
      </div>
      {expanded && hasAlertas && (
        <div className="alertas-panel">
          <p className="alertas-title"><AlertTriangle size={13} /> Alertas detectadas:</p>
          <ul>
            {r.alertas.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
};

// ── Componente de zona de drop ─────────────────────────────────────────────────
const DropZone = ({ id, accept, multiple, label, icon: Icon, color, files, onChange }) => {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = multiple ? Array.from(e.dataTransfer.files) : [e.dataTransfer.files[0]];
    onChange(dropped);
  }, [multiple, onChange]);

  return (
    <div
      className={`file-dropzone ${dragging ? 'dragging' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <Icon size={30} color={color} className="drop-icon" />
      {files && files.length > 0 ? (
        <div className="file-list">
          {files.map((f, i) => (
            <span key={i} className="file-tag">
              <CheckCircle size={12} /> {f.name} ({formatFileSize(f.size)})
            </span>
          ))}
        </div>
      ) : (
        <div>
          <p className="drop-label">{label}</p>
          <p className="drop-hint">Arrastra aquí o haz clic para seleccionar</p>
        </div>
      )}
      <input
        ref={inputRef}
        id={id}
        type="file"
        accept={accept}
        multiple={multiple}
        style={{ display: 'none' }}
        onChange={(e) => onChange(Array.from(e.target.files))}
      />
    </div>
  );
};

// ── Componente de Ranking ──────────────────────────────────────────────────
const RankingTable = ({ resultados, onDownload, onPreview }) => {
  if (!resultados || resultados.length === 0) return null;
  
  // Filtrar solo los generados correctamente y ordenar por fit_score
  const ranked = [...resultados]
    .filter(r => r.estado === 'ok')
    .sort((a, b) => (b.fit_score || 0) - (a.fit_score || 0));

  if (ranked.length === 0) return null;

  return (
    <section className="ranking-section">
      <div className="panel-title-row">
        <h2 className="panel-title">⭐ Ranking de Candidatos (Ajuste al Puesto)</h2>
      </div>
      <div className="ranking-table-container">
        <table className="ranking-table">
          <thead>
            <tr>
              <th>Pos</th>
              <th>Candidato</th>
              <th>Enfoque / Rol</th>
              <th>Fit %</th>
              <th>Semáforo de Ajuste</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((r, i) => {
              const fit = r.fit_score || 0;
              const fitClass = fit >= 80 ? 'fit-high' : fit >= 50 ? 'fit-mid' : 'fit-low';
              
              return (
                <tr key={i}>
                  <td className="rank-number">#{i + 1}</td>
                  <td className="rank-candidate">
                    <span className="rank-name">{r.nombre || r.archivo}</span>
                    <span className="rank-seniority">{r.rol_seniority}</span>
                  </td>
                  <td className="rank-focus">
                    <div style={{ 
                      fontSize: '0.85rem', 
                      color: 'var(--text-secondary)', 
                      fontWeight: '500',
                      lineHeight: '1.2'
                    }}>
                      {r.enfoque_fit || "Pendiente de análisis"}
                    </div>
                  </td>
                  <td>
                    <div className={`fit-badge ${fitClass}`}>{fit}</div>
                  </td>
                  <td className="semaforo-cell">
                    <div className="semaforo-group">
                      {r.semaforo?.cumple?.slice(0, 3).map((item, idx) => (
                        <div key={idx} className="semaforo-item cumple">
                          <div className="semaforo-dot dot-green" />
                          <span>{item}</span>
                        </div>
                      ))}
                      {r.semaforo?.gaps?.slice(0, 2).map((item, idx) => (
                        <div key={idx} className="semaforo-item gap">
                          <div className="semaforo-dot dot-red" />
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                  </td>
                  <td>
                    <div className="result-actions">
                      {(r.perfil || r.cv_id) && (
                        <button className="btn-expand" onClick={() => onPreview(r)} title="Previsualizar Perfil">
                          <Eye size={14} />
                        </button>
                      )}
                      <button className="btn-download" onClick={() => onDownload(r.ppt_id)}>
                        <Download size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
};

// ── App Principal ──────────────────────────────────────────────────────────────
function App() {
  const [cvFiles, setCvFiles] = useState([]);
  const [contexto, setContexto] = useState('');
  const [idioma, setIdioma] = useState('es');
  const [formato, setFormato] = useState('con_empresa');
  const [procesando, setProcesando] = useState(false);
  const [resultados, setResultados] = useState([]);
  const [showSugerencias, setShowSugerencias] = useState(false);
  const [errorGlobal, setErrorGlobal] = useState('');
  const [backendOk, setBackendOk] = useState(true); // Desbloqueado por defecto para emergencia
  const [connError, setConnError] = useState(null);

  // Estados para el Visor de Diapositiva
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);

  // Verificar backend al cargar (SIN BLOQUEAR)
  React.useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API}/api/health`, { mode: 'cors' });
        if (!response.ok) {
          setConnError(`Servidor respondió con código ${response.status}`);
        } else {
          setConnError(null);
        }
      } catch (err) {
        setConnError(`No se pudo conectar al motor de IA en ${API}. ${err.message}`);
        console.warn("Error de conexión inicial:", err);
      }
    };
    
    checkBackend();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorGlobal('');

    if (!cvFiles.length) { setErrorGlobal('Carga al menos un CV para procesar.'); return; }

    setProcesando(true);

    // Mostrar filas en estado "procesando"
    const inicial = cvFiles.map(f => ({ archivo: f.name, estado: 'procesando', alertas: [], ppt_id: null, error: null }));
    setResultados(inicial);

    const formData = new FormData();
    cvFiles.forEach(f => formData.append('cvs', f));
    formData.append('contexto', contexto);
    formData.append('idioma', idioma);
    formData.append('formato', formato);

    try {
      const res = await axios.post(`${API}/api/procesar`, formData, { timeout: 120000 });
      setResultados(res.data.resultados);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Error desconocido.';
      setErrorGlobal(`Error al procesar: ${msg}`);
      setResultados([]);
    } finally {
      setProcesando(false);
    }
  };

  const handleDescargar = (pptId) => {
    window.open(`${API}/api/descargar/${pptId}`, '_blank');
  };

  const handlePreview = (result) => {
    if (result.perfil) {
      setPreviewData(result.perfil);
      setShowPreview(true);
    } else if (result.cv_id) {
      // Fallback si no hay perfil completo: abrir original
      window.open(`${API}/api/cv/${result.cv_id}`, '_blank');
    }
  };

  const handleDescargarZip = () => {
    window.open(`${API}/api/descargar-zip`, '_blank');
  };

  const exitososCount = resultados.filter(r => r.estado === 'ok').length;

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-logo">
          <img src={logo} alt="Minsait Logo" className="brand-logo" />
        </div>
        <div className="header-meta">CV → PowerPoint · Personalizado Minsait</div>
      </header>

      <main className="app-main">
        {/* Banner de error de conexión (NO bloqueante) */}
        {connError && (
          <div className="alert-banner error">
            <AlertTriangle size={16} /> 
            <span><b>Atención:</b> {connError}. Asegúrate de ejecutar <code>Lanzador.bat</code>.</span>
          </div>
        )}

        {/* Sección de Ranking y Metodología */}
        {!procesando && resultados.some(r => r.estado === 'ok') && (
          <>
            <RankingTable resultados={resultados} onDownload={handleDescargar} onPreview={handlePreview} />
            <ScoringLegend contexto={contexto} />
          </>
        )}

        <div className="panel-grid">
          {/* Panel izquierdo: Formulario */}
          <section className="panel form-panel">
            <h2 className="panel-title">Configuración</h2>

            <form onSubmit={handleSubmit} id="main-form">

              {/* CVs */}
              <div className="field-group">
                <label className="field-label">
                  CVs a procesar <span className="label-hint">(PDF, DOCX, TXT, PPTX — múltiples)</span>
                </label>
                <DropZone
                  id="cv-upload"
                  accept=".pdf,.doc,.docx,.txt,.pptx"
                  multiple={true}
                  label="Carga uno o varios CVs"
                  icon={UploadCloud}
                  color="#3b82f6"
                  files={cvFiles}
                  onChange={setCvFiles}
                />
              </div>

              {/* Idioma */}
              <div className="field-group">
                <label className="field-label">
                  <Globe size={14} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
                  Idioma del perfil generado
                </label>
                <div className="idioma-selector">
                  <button
                    type="button"
                    className={`idioma-btn ${idioma === 'es' ? 'active' : ''}`}
                    onClick={() => setIdioma('es')}
                  >
                    🇪🇸 Español
                  </button>
                  <button
                    type="button"
                    className={`idioma-btn ${idioma === 'en' ? 'active' : ''}`}
                    onClick={() => setIdioma('en')}
                  >
                    🇺🇸 English
                  </button>
                </div>
                <p className="idioma-nota">
                  Nombres, universidades, certificaciones y herramientas no se traducen.
                </p>
              </div>

              {/* Formato de experiencia */}
              <div className="field-group">
                <label className="field-label">
                  <Briefcase size={14} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
                  Formato de la experiencia
                </label>
                <div className="idioma-selector">
                  <button
                    type="button"
                    className={`idioma-btn ${formato === 'con_empresa' ? 'active' : ''}`}
                    onClick={() => setFormato('con_empresa')}
                  >
                    🏢 Con empresa
                  </button>
                  <button
                    type="button"
                    className={`idioma-btn ${formato === 'sin_empresa' ? 'active' : ''}`}
                    onClick={() => setFormato('sin_empresa')}
                  >
                    🕶️ Sin empresa (anonimizado)
                  </button>
                </div>
                <p className="idioma-nota">
                  {formato === 'con_empresa'
                    ? 'Cada experiencia inicia con el nombre de la empresa tal como aparece en el CV.'
                    : 'No se nombra la empresa; se describe la actividad y se referencia el tipo/sector.'}
                  {' '}En ambos casos se resaltan en negrita las ideas clave.
                </p>
              </div>

              {/* Contexto / RFP */}
              <div className="field-group">
                <div className="label-row">
                  <label className="field-label">
                    Contexto del rol o proyecto
                    <span className="label-optional">· Opcional</span>
                  </label>
                  <button
                    type="button"
                    className="btn-sugerencias"
                    onClick={() => setShowSugerencias(!showSugerencias)}
                  >
                    <Info size={13} /> ¿Qué poner aquí?
                  </button>
                </div>

                {showSugerencias && (
                  <div className="sugerencias-box">
                    <p className="sugerencias-title">Preguntas guía para este campo:</p>
                    <ul>
                      <li>¿Qué tipo de proyecto es? (transformación digital, auditoría, ERP...)</li>
                      <li>¿Qué skills son indispensables para el rol?</li>
                      <li>¿Qué sector tiene el cliente? (banca, retail, gobierno...)</li>
                      <li>¿Hay una seniority mínima requerida?</li>
                      <li>¿Qué herramientas o metodologías son prioritarias?</li>
                    </ul>
                    <p className="sugerencias-nota">La IA priorizará experiencia relevante según este contexto, sin inventar nada.</p>
                  </div>
                )}

                <textarea
                  rows="4"
                  placeholder="Pega aquí el RFP, descripción del rol o requisitos clave del proyecto..."
                  value={contexto}
                  onChange={(e) => setContexto(e.target.value)}
                />
              </div>

              {errorGlobal && (
                <div className="alert-inline error">
                  <XCircle size={14} /> {errorGlobal}
                </div>
              )}

              <button
                type="submit"
                className="btn-primary"
                disabled={procesando || backendOk === false}
                id="btn-procesar"
              >
                {procesando ? (
                  <><Loader size={16} className="spin" /> Procesando CVs...</>
                ) : (
                  <><UploadCloud size={16} /> Generar Perfiles PPT</>
                )}
              </button>
            </form>
          </section>

          {/* Panel derecho: Resultados */}
          <section className="panel results-panel">
            <div className="panel-title-row">
              <h2 className="panel-title">Resultados</h2>
              {exitososCount >= 2 && (
                <button className="btn-zip" onClick={handleDescargarZip}>
                  <Download size={14} /> Descargar ZIP ({exitososCount})
                </button>
              )}
            </div>

            {resultados.length === 0 ? (
              <div className="empty-state">
                <FileText size={40} className="empty-icon" />
                <p>Los perfiles generados aparecerán aquí.</p>
                <p className="empty-hint">Configura los archivos y presiona "Generar Perfiles PPT".</p>
              </div>
            ) : (
              <div className="results-list">
                {resultados.map((r, i) => (
                  <ResultRow key={i} r={r} onDownload={handleDescargar} onPreview={handlePreview} />
                ))}
              </div>
            )}
          </section>
        </div>
      </main>

      <footer className="app-footer">
        Staffing AI Builder v2 · Basado en evidencia documental · No se inventa información · <span style={{ opacity: 0.8, fontWeight: 500 }}>Creado por Nelson Bernal C.</span>
      </footer>

      {showPreview && (
        <SlidePreview 
          perfil={previewData} 
          onClose={() => setShowPreview(false)} 
        />
      )}
    </div>
  );
}

export default App;
