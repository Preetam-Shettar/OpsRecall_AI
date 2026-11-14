import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { formatDate } from '../utils/formatters';

export default function IncidentTimeline({ incidentId }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterActor, setFilterActor] = useState('all'); // 'all', 'ai', 'engineer'
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (incidentId) {
      loadTimeline();
    }
  }, [incidentId]);

  async function loadTimeline() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getIncidentTimeline(incidentId);
      setEvents(data || []);
    } catch (err) {
      setError(err.message || 'Failed to load incident timeline');
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    setIsRefreshing(true);
    try {
      const data = await api.getIncidentTimeline(incidentId);
      setEvents(data || []);
    } catch (err) {
      setError(err.message || 'Failed to refresh timeline');
    } finally {
      setIsRefreshing(false);
    }
  }

  const filteredEvents = events.filter((e) => {
    if (filterActor === 'ai') return e.actor_type === 'ai';
    if (filterActor === 'engineer') return e.actor_type === 'engineer';
    return true;
  });

  function getEventIcon(eventType) {
    switch (eventType) {
      case 'incident_created':
        return '🚨';
      case 'analysis_completed':
        return '🧠';
      case 'action_created':
        return '📋';
      case 'actions_imported':
        return '⚡';
      case 'action_started':
        return '⏳';
      case 'action_completed':
        return '✅';
      case 'action_blocked':
        return '⛔';
      case 'action_reset':
        return '↺';
      case 'engineer_assigned':
        return '👤';
      case 'resolution_submitted':
        return '📝';
      case 'resolution_verified':
        return '🛡️';
      case 'incident_resolved':
        return '🏁';
      default:
        return '📌';
    }
  }

  return (
    <div className="incident-timeline-panel">
      <div className="timeline-header">
        <div className="timeline-title-group">
          <span className="timeline-badge">AUDIT TRAIL</span>
          <h4>Incident Chronology &amp; Provenance</h4>
        </div>

        <div className="timeline-header-controls">
          <div className="timeline-filter-pills">
            <button
              type="button"
              className={`timeline-filter-pill ${filterActor === 'all' ? 'active' : ''}`}
              onClick={() => setFilterActor('all')}
            >
              All Events ({events.length})
            </button>
            <button
              type="button"
              className={`timeline-filter-pill ${filterActor === 'engineer' ? 'active' : ''}`}
              onClick={() => setFilterActor('engineer')}
            >
              👷 Engineer ({events.filter((e) => e.actor_type === 'engineer').length})
            </button>
            <button
              type="button"
              className={`timeline-filter-pill ${filterActor === 'ai' ? 'active' : ''}`}
              onClick={() => setFilterActor('ai')}
            >
              🤖 AI Actions ({events.filter((e) => e.actor_type === 'ai').length})
            </button>
          </div>

          <button
            type="button"
            className="timeline-refresh-btn"
            onClick={handleRefresh}
            disabled={isRefreshing}
            title="Refresh event chronology"
          >
            {isRefreshing ? 'Syncing…' : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="page-error-alert">
          <span>⚠️ {error}</span>
        </div>
      )}

      {loading ? (
        <div className="timeline-loading-state">
          <div className="loading-spinner-small" />
          <p>Loading chronological event history…</p>
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="timeline-empty-card">
          <span className="empty-icon">⏱️</span>
          <p>No timeline events match the filter.</p>
        </div>
      ) : (
        <div className="timeline-events-stream">
          {filteredEvents.map((evt, idx) => {
            const isAI = evt.actor_type === 'ai';
            const isEngineer = evt.actor_type === 'engineer';
            const isLast = idx === filteredEvents.length - 1;

            return (
              <div
                key={evt.id || idx}
                className={`timeline-item-row actor-${evt.actor_type} event-${evt.event_type}`}
              >
                <div className="timeline-track-col">
                  <div className={`timeline-marker-dot ${isAI ? 'dot-ai' : isEngineer ? 'dot-engineer' : 'dot-system'}`}>
                    <span className="marker-emoji">{getEventIcon(evt.event_type)}</span>
                  </div>
                  {!isLast && <div className="timeline-connector-line" />}
                </div>

                <div className="timeline-content-card">
                  <div className="timeline-card-header">
                    <div className="timeline-actor-badge-group">
                      <span className={`actor-type-pill ${isAI ? 'pill-ai' : isEngineer ? 'pill-engineer' : 'pill-system'}`}>
                        {isAI ? '🤖 OpsRecall AI' : isEngineer ? `👷 ${evt.actor}` : '⚙️ System'}
                      </span>
                      <span className="timeline-event-name">{evt.event_type.replace('_', ' ').toUpperCase()}</span>
                    </div>

                    <time className="timeline-timestamp" dateTime={evt.created_at} title={evt.created_at}>
                      {formatDate(evt.created_at)}
                    </time>
                  </div>

                  <p className="timeline-description-text">{evt.description}</p>

                  {evt.related_action_id && (
                    <div className="timeline-action-tag">
                      <span className="tag-label">Related Action:</span>
                      <code className="tag-code">{evt.related_action_id}</code>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
