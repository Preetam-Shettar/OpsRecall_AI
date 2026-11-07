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
}) {
  const viewTitles = {
    dashboard: 'System Overview & Telemetry',
    newIncident: 'New Incident Investigation',
    history: 'Incident Knowledge Base',
    memory: 'Hindsight Memory Bank Explorer',
    details: 'Incident Diagnosis & Resolution',
  };

  const themes = [
    { id: 'obsidian', label: 'Obsidian Cyan', icon: '⚡' },
    { id: 'emerald', label: 'Emerald Ops', icon: '🌿' },
    { id: 'synth', label: 'Midnight Synth', icon: '🔮' },
    { id: 'slate', label: 'Slate Navy', icon: '🌊' },
  ];

  return (
    <header className="navbar">
      <div className="navbar-left">
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
