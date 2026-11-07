import React from 'react';
import StatCard from '../components/StatCard';
import IncidentCard from '../components/IncidentCard';

export default function Dashboard({
  dashboard,
  recentIncidents = [],
  onNavigateNew,
  onNavigateHistory,
  onSelectIncident,
}) {
  const total = dashboard?.total_incidents || 0;
  const resolved = dashboard?.resolved_incidents || 0;
  const openCount = dashboard?.open_incidents || Math.max(total - resolved, 0);
  const memories = dashboard?.stored_memories || 0;

  return (
    <div className="page dashboard-page">
      <div className="page-header">
        <div>
          <h2>Operational Health &amp; Memory Overview</h2>
          <p className="page-subtitle">
            Continuous incident triage powered by persistent Hindsight memory banks.
          </p>
        </div>
        <button
          type="button"
          className="primary-action-btn"
          onClick={onNavigateNew}
        >
          ⚡ Investigate New Incident
        </button>
      </div>

      {/* Stats Cards Row */}
      <section className="stats-grid">
        <StatCard
          label="Total Incidents"
          value={total}
          subtitle="Processed by agent"
          icon="📋"
          highlightColor="blue"
        />
        <StatCard
          label="Verified Resolutions"
          value={resolved}
          subtitle="Confirmed by engineers"
          icon="✅"
          highlightColor="green"
        />
        <StatCard
          label="Active / Open"
          value={openCount}
          subtitle="Awaiting resolution"
          icon="⏳"
          highlightColor="amber"
        />
        <StatCard
          label="Hindsight Memories"
          value={memories}
          subtitle="Retained learning records"
          icon="🧠"
          highlightColor="purple"
        />
      </section>

      {/* Memory Value Spotlight */}
      <div className="memory-spotlight-card">
        <div className="spotlight-left">
          <span className="spotlight-badge">🧠 Persistent Learning Loop</span>
          <h3>How Hindsight Prevents Duplicate Work</h3>
          <p>
            When an engineer verifies an incident resolution, OpsRecall AI saves a structured memory to Hindsight.
            When a future incident occurs with similar symptoms or error traces, Hindsight recalls the historical fix as contextual guidance for the LLM.
          </p>
        </div>
        <div className="spotlight-steps">
          <div className="step-box">
            <span className="step-num">1</span>
            <strong>Retain</strong>
            <p>Engineer-confirmed root causes stored permanently.</p>
          </div>
          <div className="step-box">
            <span className="step-num">2</span>
            <strong>Recall</strong>
            <p>Past fixes retrieved instantly on similar symptoms.</p>
          </div>
          <div className="step-box">
            <span className="step-num">3</span>
            <strong>Reflect</strong>
            <p>Synthesizes recurring failure patterns across services.</p>
          </div>
        </div>
      </div>

      {/* Recent Incidents Section */}
      <section className="dashboard-section">
        <div className="section-header-row">
          <div className="section-title-group">
            <h3>Recent Incidents</h3>
            <span className="section-note">Most recent operational telemetry</span>
          </div>
          {onNavigateHistory && total > 0 && (
            <button
              type="button"
              className="view-all-link-btn"
              onClick={onNavigateHistory}
            >
              View All History ({total}) →
            </button>
          )}
        </div>

        {recentIncidents.length === 0 ? (
          <div className="empty-card">
            <p>No incidents recorded yet.</p>
            <button
              type="button"
              className="secondary-btn"
              onClick={onNavigateNew}
            >
              Submit First Incident (Scenario A)
            </button>
          </div>
        ) : (
          <div className="incidents-grid">
            {recentIncidents.slice(0, 4).map((incident) => (
              <IncidentCard
                key={incident.id}
                incident={incident}
                onSelect={onSelectIncident}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
