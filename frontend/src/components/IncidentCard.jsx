import React from 'react';
import { formatDate, formatStatus } from '../utils/formatters';

export default function IncidentCard({ incident, isSelected, onSelect }) {
  const statusInfo = formatStatus(incident.status);
  const hasResolution = !!incident.resolution;

  return (
    <div
      className={`incident-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(incident)}
      role="button"
      tabIndex={0}
    >
      <div className="incident-card-top">
        <span className="incident-id">{incident.id}</span>
        <span className={`status-pill ${statusInfo.badgeClass}`}>
          {statusInfo.label}
        </span>
      </div>

      <h4 className="incident-card-title">{incident.title}</h4>

      <div className="incident-card-meta">
        <span className="meta-tag service-tag">{incident.service}</span>
        <span className="meta-tag env-tag">{incident.environment}</span>
        {hasResolution && (
          <span className="meta-tag verified-tag">✓ Memory Saved</span>
        )}
      </div>

      <div className="incident-card-bottom">
        <span className="incident-date">{formatDate(incident.created_at)}</span>
      </div>
    </div>
  );
}
