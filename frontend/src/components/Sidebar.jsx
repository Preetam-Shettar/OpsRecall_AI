import React from 'react';

export default function Sidebar({ activeView, setActiveView, counts = {} }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'newIncident', label: 'New Incident', icon: '⚡' },
    { id: 'history', label: 'Incident History', icon: '📁', count: counts.total_incidents },
    { id: 'memory', label: 'Hindsight Memory', icon: '🧠', count: counts.stored_memories },
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-logo">
          <div className="brand-icon">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="brand-svg"
            >
              <path
                d="M13 2L3.5 13.5H11.5L10 22L20.5 9.5H12.5L13 2Z"
                fill="#ffffff"
                stroke="#ffffff"
                strokeWidth="1.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div>
            <h1 className="brand-name">OpsRecall AI</h1>
            <p className="brand-tagline">Incident Response Agent</p>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveView(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.count !== undefined && item.count > 0 && (
                <span className="nav-count">{item.count}</span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="memory-info-card">
          <div className="memory-info-header">
            <span className="memory-icon">🧠</span>
            <strong>Persistent Memory</strong>
          </div>
          <p className="memory-info-text">
            Powered by <strong>Hindsight</strong> retain &amp; recall to prevent repeated root-cause investigations.
          </p>
        </div>
      </div>
    </aside>
  );
}
