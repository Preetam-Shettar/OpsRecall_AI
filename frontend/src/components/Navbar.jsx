import React from 'react';

export default function Navbar({ activeView, backendHealthy }) {
  const viewTitles = {
    dashboard: 'System Overview & Telemetry',
    newIncident: 'New Incident Investigation',
    history: 'Incident Knowledge Base',
    memory: 'Hindsight Memory Bank Explorer',
    details: 'Incident Diagnosis & Resolution',
  };

  return (
    <header className="navbar">
      <div className="navbar-left">
        <h2 className="navbar-title">{viewTitles[activeView] || 'Incident Operations'}</h2>
      </div>

      <div className="navbar-right">
        <div className="memory-badge">
          <span className="dot dot-hindsight"></span>
          <span>Hindsight Bank: <strong>opsrecall-incidents</strong></span>
        </div>
        <div className={`health-badge ${backendHealthy ? 'healthy' : 'degraded'}`}>
          <span className={`dot ${backendHealthy ? 'dot-green' : 'dot-red'}`}></span>
          <span>{backendHealthy ? 'Backend Connected' : 'Connecting to API...'}</span>
        </div>
      </div>
    </header>
  );
}
