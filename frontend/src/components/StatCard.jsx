import React from 'react';

export default function StatCard({ label, value, subtitle, icon, highlightColor = 'blue', badge, onClick }) {
  return (
    <div
      className={`stat-card stat-${highlightColor} ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="stat-card-header">
        <span className="stat-card-label">{label}</span>
        <div className="stat-card-top-right">
          {badge && <span className="stat-card-badge">{badge}</span>}
          {icon && <span className="stat-card-icon">{icon}</span>}
        </div>
      </div>
      <div className="stat-card-body">
        <span className="stat-card-value">{value}</span>
        {subtitle && <span className="stat-card-subtitle">{subtitle}</span>}
      </div>
    </div>
  );
}
