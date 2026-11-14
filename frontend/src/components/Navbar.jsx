import React from 'react';

export default function Navbar({
  activeView,
  backendHealthy,
  canGoBack,
  onBack,
  onRefresh,
  isRefreshing,
  onToggleSidebar,
}) {
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
        {/* Mobile / Tablet Menu Button */}
        <button
          type="button"
          className="sidebar-toggle-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
          title="Toggle Navigation Menu"
        >
          <span className="hamburger-icon">☰</span>
        </button>

        {canGoBack && (
          <button
            type="button"
            className="navbar-back-btn"
            onClick={onBack}
            title="Go back to previous screen"
          >
            ← Back
          </button>
        )}
        <h2 className="navbar-title">{viewTitles[activeView] || 'Incident Operations'}</h2>
      </div>

      <div className="navbar-right">
        {/* Refresh Button */}
        <button
          type="button"
          className={`navbar-refresh-btn ${isRefreshing ? 'refreshing' : ''}`}
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh incident telemetry and connection status"
        >
          <span className="refresh-icon">🔄</span>
          <span className="refresh-label">{isRefreshing ? 'Syncing…' : 'Refresh'}</span>
        </button>

        {/* Hindsight Bank Badge */}
        <div className="memory-badge" title="Active Hindsight Memory Bank: opsrecall-incidents">
          <span className="dot dot-hindsight"></span>
          <span className="badge-text-full">Hindsight Bank: <strong>opsrecall-incidents</strong></span>
          <span className="badge-text-short">Bank: <strong>opsrecall</strong></span>
        </div>

        {/* Backend Connectivity Badge */}
        <div className={`health-badge ${backendHealthy ? 'healthy' : 'degraded'}`} title={backendHealthy ? 'FastAPI Backend Online' : 'FastAPI Backend Offline'}>
          <span className={`dot ${backendHealthy ? 'dot-green' : 'dot-red'}`}></span>
          <span className="badge-text-full">{backendHealthy ? 'Backend Connected' : 'Connecting to API...'}</span>
          <span className="badge-text-short">{backendHealthy ? 'Online' : 'Offline'}</span>
        </div>
      </div>
    </header>
  );
}
