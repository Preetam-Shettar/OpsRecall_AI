import React from 'react';

export default function StatCard({ label, value, subtitle, icon, highlightColor = 'blue' }) {
  return (
    <div className={`stat-card stat-${highlightColor}`}>
      <div className="stat-card-header">
        <span className="stat-card-label">{label}</span>
        {icon && <span className="stat-card-icon">{icon}</span>}
      </div>
      <div className="stat-card-body">
        <span className="stat-card-value">{value}</span>
        {subtitle && <span className="stat-card-subtitle">{subtitle}</span>}
      </div>
    </div>
  );
}
