import React, { useState } from 'react';
import { formatDate, formatStatus } from '../utils/formatters';

export default function IncidentHistory({ incidents = [], onSelectIncident, onNavigateNew }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredIncidents = incidents.filter((incident) => {
    const matchesSearch =
      !searchTerm ||
      incident.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      incident.service?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      incident.id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      incident.description?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === 'all' || incident.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="page incident-history-page">
      <div className="page-header">
        <div>
          <h2>Incident Knowledge Base</h2>
          <p className="page-subtitle">
            All recorded system anomalies, AI analyses, and engineer-verified solutions.
          </p>
        </div>
        <button type="button" className="primary-action-btn" onClick={onNavigateNew}>
          + New Incident
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="filter-bar">
        <div className="search-input-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search by title, service name, ID, or keywords..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="status-filters">
          <button
            type="button"
            className={`filter-pill ${statusFilter === 'all' ? 'active' : ''}`}
            onClick={() => setStatusFilter('all')}
          >
            All ({incidents.length})
          </button>
          <button
            type="button"
            className={`filter-pill ${statusFilter === 'resolved' ? 'active' : ''}`}
            onClick={() => setStatusFilter('resolved')}
          >
            Resolved ({incidents.filter((i) => i.status === 'resolved').length})
          </button>
          <button
            type="button"
            className={`filter-pill ${statusFilter === 'analyzed' ? 'active' : ''}`}
            onClick={() => setStatusFilter('analyzed')}
          >
            Open / Analyzed ({incidents.filter((i) => i.status !== 'resolved').length})
          </button>
        </div>
      </div>

      {/* Incidents Table / List */}
      {filteredIncidents.length === 0 ? (
        <div className="empty-history-box">
          <p>No incidents match your current filter.</p>
        </div>
      ) : (
        <div className="history-table-container">
          <table className="history-table">
            <thead>
              <tr>
                <th>Incident ID</th>
                <th>Title &amp; Symptoms</th>
                <th>Service</th>
                <th>Environment</th>
                <th>Status</th>
                <th>Memory Status</th>
                <th>Detected At</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredIncidents.map((incident) => {
                const statusInfo = formatStatus(incident.status);
                const isResolved = incident.status === 'resolved';

                return (
                  <tr key={incident.id} onClick={() => onSelectIncident(incident)} className="clickable-row">
                    <td className="id-cell">{incident.id}</td>
                    <td className="title-cell">
                      <strong>{incident.title}</strong>
                      <p className="desc-preview">{incident.description?.substring(0, 75)}...</p>
                    </td>
                    <td>
                      <span className="service-tag">{incident.service}</span>
                    </td>
                    <td>
                      <span className="env-tag">{incident.environment}</span>
                    </td>
                    <td>
                      <span className={`status-pill ${statusInfo.badgeClass}`}>
                        {statusInfo.label}
                      </span>
                    </td>
                    <td>
                      {isResolved ? (
                        <span className="memory-badge-saved">✓ Retained in Hindsight</span>
                      ) : (
                        <span className="memory-badge-pending">Pending Resolution</span>
                      )}
                    </td>
                    <td className="date-cell">{formatDate(incident.created_at)}</td>
                    <td>
                      <button
                        type="button"
                        className="table-action-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectIncident(incident);
                        }}
                      >
                        Inspect →
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
