import React from 'react';
import { Database, Briefcase, User, Factory, Info } from 'lucide-react';

const ScoringLegend = ({ contexto }) => {
  // Extraer palabras clave simples del contexto para personalizar
  const keywords = contexto 
    ? contexto.split(/[\s,.]+/).filter(w => w.length > 5).slice(0, 3).join(', ')
    : 'Skills estándar';

  const criteria = [
    { label: 'Herramientas', weight: '40%', flex: 40, color: '#4c111f', desc: `Requerimientos técnicos: ${keywords}...` },
    { label: 'Experiencia', weight: '30%', flex: 30, color: '#7a1c32', desc: 'Funciones y responsabilidades' },
    { label: 'Seniority', weight: '20%', flex: 20, color: '#a82745', desc: 'Trayectoria total' },
    { label: 'Industria', weight: '10%', flex: 10, color: '#d63258', desc: 'Sector' }
  ];

  return (
    <section className="scoring-legend-compact">
      <div className="legend-bar-container">
        <div className="legend-bar">
          {criteria.map((item, idx) => (
            <div 
              key={idx} 
              className="legend-segment" 
              style={{ flex: item.flex, backgroundColor: item.color }}
              title={`${item.label}: ${item.weight}`}
            >
              <span className="segment-label">{item.weight}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="legend-labels-row">
        {criteria.map((item, idx) => (
          <div key={idx} className="label-col" style={{ flex: item.flex }}>
            <div className="label-text-box">
              <div className="label-header-compact">
                <div className="label-dot" style={{ backgroundColor: item.color }} />
                <span className="label-name">{item.label}</span>
              </div>
              <span className="label-desc-compact">{item.desc}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default ScoringLegend;
