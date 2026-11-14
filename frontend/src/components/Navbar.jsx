import React from 'react';

export default function Navbar({
  activeView,
  backendHealthy,
  theme,
  onThemeChange,
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

  const themes = [
    { id: 'signal', label: 'Signal / Field Notes', icon: '📡' },
    { id: 'obsidian', label: 'Obsidian Ink', icon: '⚡' },
    { id: 'emerald', label: 'Emerald Field', icon: '🌿' },
    { id: 'synth', label: 'Amber Synth', icon: '🔮' },
    { id: 'slate', label: 'Slate Technical', icon: '🌊' },
  ];

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

        {/* Theme Selector */}
        <div className="theme-selector-pill">
          <span className="theme-selector-label">Theme:</span>
          <select
            value={theme}
            onChange={(e) => onThemeChange(e.target.value)}
            className="theme-select-input"
            aria-label="Color Theme Selector"
          >
            {themes.map((t) => (
              <option key={t.id} value={t.id}>
                {t.icon} {t.label}
              </option>
            ))}
          </select>
        </div>

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
