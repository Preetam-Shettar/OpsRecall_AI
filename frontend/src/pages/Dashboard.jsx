import React, { useState } from 'react';
import StatCard from '../components/StatCard';
import IncidentCard from '../components/IncidentCard';

export default function Dashboard({
  dashboard,
  recentIncidents = [],
  onNavigateNew,
  onNavigateHistory,
  onNavigateMemory,
  onSelectIncident,
  onRefresh,
  isRefreshing,
}) {
  const [incidentFilter, setIncidentFilter] = useState('all');

  // Overview Counts
  const total = dashboard?.total_incidents || 0;
  const resolved = dashboard?.resolved_incidents || 0;
  const openCount = dashboard?.open_incidents ?? Math.max(total - resolved, 0);
  const criticalCount = dashboard?.critical_incidents ?? 0;
  const memories = dashboard?.stored_memories || 0;

  // Analytics Data
  const severityMap = dashboard?.by_severity || { critical: 0, high: 0, medium: 0, low: 0 };
  const statusMap = dashboard?.by_status || {};
  const services = dashboard?.by_service || [];
  const resolutionTrends = dashboard?.resolution_trends || [];

  // Operational Insights Data
  const insights = dashboard?.operational_insights || {};
  const mostAffected = insights.most_affected_services || [];
  const incidentTypes = insights.frequently_occurring_types || [];
  const avgResTime = insights.avg_resolution_time || {
    available: false,
    display: 'Unavailable',
    note: 'No resolution telemetry available yet.',
  };
  const recurringPatterns = insights.recurring_patterns || [];
  const actionsSummary = dashboard?.actions_summary || insights?.actions_summary || {};

  // Memory Intelligence Data
  const memoryIntel = dashboard?.memory_intelligence || {};
  const memoryStatus = memoryIntel.memory_system_status || {
    status: 'online',
    mode: 'Local SQLite Fallback',
    bank_id: 'opsrecall-incidents',
    verified_only: true,
  };
  const frequentlyRecalled = memoryIntel.frequently_recalled || [];
  const hasRecallStats = memoryIntel.has_recall_statistics;

  // Filter recent incidents
  const filteredIncidents = recentIncidents.filter((incident) => {
    if (incidentFilter === 'critical') {
      return (incident.severity || '').toLowerCase() === 'critical';
    }
    if (incidentFilter === 'active') {
      return (incident.status || '').toLowerCase() !== 'resolved';
    }
    if (incidentFilter === 'resolved') {
      return (incident.status || '').toLowerCase() === 'resolved';
    }
    return true;
  });

  // Calculate percentages for severity distribution
  const severityTotal = (severityMap.critical || 0) + (severityMap.high || 0) + (severityMap.medium || 0) + (severityMap.low || 0) || total || 1;
  const sevPct = {
    critical: Math.round(((severityMap.critical || 0) / severityTotal) * 100),
    high: Math.round(((severityMap.high || 0) / severityTotal) * 100),
    medium: Math.round(((severityMap.medium || 0) / severityTotal) * 100),
    low: Math.round(((severityMap.low || 0) / severityTotal) * 100),
  };

  return (
    <div className="page dashboard-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h2>Incident Intelligence Dashboard</h2>
          <p className="page-subtitle">
            Autonomous incident diagnosis, cross-service failure correlation, and persistent Hindsight memory intelligence.
          </p>
        </div>
        <div className="header-actions-group">
          {onRefresh && (
            <button
              type="button"
              className="secondary-btn refresh-btn"
              onClick={onRefresh}
              disabled={isRefreshing}
              title="Refresh telemetry"
            >
              {isRefreshing ? 'Refreshing...' : '🔄 Refresh'}
            </button>
          )}
          <button
            type="button"
            className="primary-action-btn"
            onClick={onNavigateNew}
          >
            ⚡ Investigate New Incident
          </button>
        </div>
      </div>

      {/* 1. Incident Overview Cards */}
      <section className="stats-grid">
        <StatCard
          label="Total Incidents"
          value={total}
          subtitle="Processed by OpsRecall"
          icon="📋"
          highlightColor="blue"
        />
        <StatCard
          label="Active Incidents"
          value={openCount}
          subtitle="Awaiting resolution"
          icon="⏳"
          highlightColor="amber"
        />
        <StatCard
          label="Resolved Incidents"
          value={resolved}
          subtitle="Confirmed & mitigated"
          icon="✅"
          highlightColor="green"
        />
        <StatCard
          label="Critical Incidents"
          value={criticalCount}
          subtitle="High-impact production events"
          icon="🔥"
          highlightColor="red"
        />
      </section>

      {/* 2. Incident Analytics */}
      <div className="dashboard-grid-2">
        {/* Severity & Status Distribution Card */}
        <div className="intelligence-card">
          <div className="intel-card-header">
            <div className="intel-card-title">
              <span className="intel-card-icon">📊</span>
              <div>
                <h4>Incident Distribution</h4>
                <span className="intel-card-sub">Severity breakdown &amp; lifecycle status</span>
              </div>
            </div>
          </div>

          <div className="intel-card-body">
            {/* Severity Segmented Bar */}
            <div className="metric-group">
              <div className="metric-label-row">
                <span className="metric-title">Severity Breakdown</span>
                <span className="metric-meta">{total} total incidents</span>
              </div>
              <div className="distribution-bar">
                {(severityMap.critical || 0) > 0 && (
                  <div
                    className="dist-segment dist-critical"
                    style={{ width: `${Math.max(sevPct.critical, 12)}%` }}
                    title={`Critical: ${severityMap.critical} (${sevPct.critical}%)`}
                  >
                    <span>{severityMap.critical}</span>
                  </div>
                )}
                {(severityMap.high || 0) > 0 && (
                  <div
                    className="dist-segment dist-high"
                    style={{ width: `${Math.max(sevPct.high, 12)}%` }}
                    title={`High: ${severityMap.high} (${sevPct.high}%)`}
                  >
                    <span>{severityMap.high}</span>
                  </div>
                )}
                {(severityMap.medium || 0) > 0 && (
                  <div
                    className="dist-segment dist-medium"
                    style={{ width: `${Math.max(sevPct.medium, 12)}%` }}
                    title={`Medium: ${severityMap.medium} (${sevPct.medium}%)`}
                  >
                    <span>{severityMap.medium}</span>
                  </div>
                )}
                {(severityMap.low || 0) > 0 && (
                  <div
                    className="dist-segment dist-low"
                    style={{ width: `${Math.max(sevPct.low, 12)}%` }}
                    title={`Low: ${severityMap.low} (${sevPct.low}%)`}
                  >
                    <span>{severityMap.low}</span>
                  </div>
                )}
                {total === 0 && (
                  <div className="dist-segment dist-empty" style={{ width: '100%' }}>
                    <span>No incidents recorded</span>
                  </div>
                )}
              </div>

              {/* Legend */}
              <div className="severity-legend-grid">
                <div className="legend-item">
                  <span className="legend-dot dot-critical" />
                  <span className="legend-label">Critical:</span>
                  <strong>{severityMap.critical || 0}</strong>
                  <span className="legend-pct">({total > 0 ? sevPct.critical : 0}%)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot dot-high" />
                  <span className="legend-label">High:</span>
                  <strong>{severityMap.high || 0}</strong>
                  <span className="legend-pct">({total > 0 ? sevPct.high : 0}%)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot dot-medium" />
                  <span className="legend-label">Medium:</span>
                  <strong>{severityMap.medium || 0}</strong>
                  <span className="legend-pct">({total > 0 ? sevPct.medium : 0}%)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot dot-low" />
                  <span className="legend-label">Low:</span>
                  <strong>{severityMap.low || 0}</strong>
                  <span className="legend-pct">({total > 0 ? sevPct.low : 0}%)</span>
                </div>
              </div>
            </div>

            {/* Lifecycle Status Distribution */}
            <div className="metric-group mt-3">
              <div className="metric-label-row">
                <span className="metric-title">Lifecycle Status</span>
              </div>
              <div className="status-badges-row">
                <div className="status-metric-pill pill-resolved">
                  <span className="pill-dot" />
                  <span className="pill-text">Resolved</span>
                  <span className="pill-count">{statusMap.resolved || 0}</span>
                </div>
                <div className="status-metric-pill pill-analyzed">
                  <span className="pill-dot" />
                  <span className="pill-text">Analyzed</span>
                  <span className="pill-count">{statusMap.analyzed || 0}</span>
                </div>
                {statusMap.mitigated !== undefined && (
                  <div className="status-metric-pill pill-mitigated">
                    <span className="pill-dot" />
                    <span className="pill-text">Mitigated</span>
                    <span className="pill-count">{statusMap.mitigated || 0}</span>
                  </div>
                )}
                {statusMap.new !== undefined && (
                  <div className="status-metric-pill pill-new">
                    <span className="pill-dot" />
                    <span className="pill-text">New</span>
                    <span className="pill-count">{statusMap.new || 0}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Incidents by Service Card */}
        <div className="intelligence-card">
          <div className="intel-card-header">
            <div className="intel-card-title">
              <span className="intel-card-icon">🏢</span>
              <div>
                <h4>Incidents by Service</h4>
                <span className="intel-card-sub">Service load and resolution health</span>
              </div>
            </div>
          </div>

          <div className="intel-card-body">
            {services.length === 0 ? (
              <div className="empty-intel-state">
                <p>No service telemetry recorded yet.</p>
              </div>
            ) : (
              <div className="service-breakdown-list">
                {services.map((svc) => {
                  const svcPct = total > 0 ? Math.round((svc.total / total) * 100) : 0;
                  const resPct = svc.total > 0 ? Math.round((svc.resolved / svc.total) * 100) : 0;
                  return (
                    <div key={svc.service} className="service-row-item">
                      <div className="service-row-top">
                        <div className="service-name-group">
                          <span className="service-code-badge">{svc.service}</span>
                          {svc.critical > 0 && (
                            <span className="service-critical-tag">
                              {svc.critical} Critical
                            </span>
                          )}
                        </div>
                        <div className="service-counts-group">
                          <span className="service-total-count">{svc.total} incident{svc.total !== 1 ? 's' : ''}</span>
                          <span className="service-pct-tag">({svcPct}% total)</span>
                        </div>
                      </div>
                      <div className="service-progress-container">
                        <div
                          className="service-progress-bar"
                          style={{ width: `${svcPct}%` }}
                        />
                      </div>
                      <div className="service-row-bottom">
                        <span className="service-health-note">
                          {svc.resolved} resolved ({resPct}%) · {svc.active} active
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Resolution Trends Card */}
      <div className="intelligence-card full-width-card mb-4">
        <div className="intel-card-header">
          <div className="intel-card-title">
            <span className="intel-card-icon">📈</span>
            <div>
              <h4>Incident &amp; Resolution Trends</h4>
              <span className="intel-card-sub">Chronological timeline of incident creation vs resolution verification</span>
            </div>
          </div>
        </div>

        <div className="intel-card-body">
          {resolutionTrends.length === 0 ? (
            <div className="empty-intel-state">
              <p>No historical timestamps available to compute resolution trends.</p>
            </div>
          ) : (
            <div className="trends-timeline-grid">
              {resolutionTrends.map((t) => (
                <div key={t.date} className="trend-timeline-cell">
                  <div className="trend-date-header">{t.date}</div>
                  <div className="trend-bars-wrapper">
                    <div className="trend-bar-row">
                      <span className="trend-label">Created:</span>
                      <div className="trend-bar-track">
                        <div
                          className="trend-bar-fill fill-created"
                          style={{ width: `${Math.min(t.created * 40, 100)}%` }}
                        />
                      </div>
                      <span className="trend-val">{t.created}</span>
                    </div>
                    <div className="trend-bar-row">
                      <span className="trend-label">Resolved:</span>
                      <div className="trend-bar-track">
                        <div
                          className="trend-bar-fill fill-resolved"
                          style={{ width: `${Math.min(t.resolved * 40, 100)}%` }}
                        />
                      </div>
                      <span className="trend-val">{t.resolved}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 3. Operational Insights */}
      <div className="section-title-group mb-2">
        <h3>Operational Insights</h3>
        <span className="section-note">Systemic diagnostics derived from incident logs, causes, and resolution data</span>
      </div>

      <div className="insights-grid-4">
        {/* Most Affected Services */}
        <div className="insight-box">
          <div className="insight-box-header">
            <span className="insight-icon">🎯</span>
            <h5>Most Affected Services</h5>
          </div>
          {mostAffected.length === 0 ? (
            <p className="insight-empty">No affected services data</p>
          ) : (
            <ul className="insight-list">
              {mostAffected.map((s, idx) => (
                <li key={s.service} className="insight-list-item">
                  <span className="rank-badge">#{idx + 1}</span>
                  <span className="insight-svc-name">{s.service}</span>
                  <span className="insight-svc-count">{s.total} incidents</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Frequently Occurring Incident Types */}
        <div className="insight-box">
          <div className="insight-box-header">
            <span className="insight-icon">🔍</span>
            <h5>Frequent Incident Types</h5>
          </div>
          {incidentTypes.length === 0 ? (
            <p className="insight-empty">No incident types categorized yet</p>
          ) : (
            <ul className="insight-list">
              {incidentTypes.slice(0, 3).map((item) => (
                <li key={item.type} className="insight-list-item-type">
                  <div className="type-item-top">
                    <span className="type-name">{item.type}</span>
                    <span className="type-count">{item.count} ({item.percentage}%)</span>
                  </div>
                  <div className="type-bar-track">
                    <div
                      className="type-bar-fill"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Average Resolution Time */}
        <div className="insight-box">
          <div className="insight-box-header">
            <span className="insight-icon">⏱️</span>
            <h5>Mean Resolution Time</h5>
          </div>
          <div className="resolution-time-display">
            {avgResTime.available ? (
              <>
                <span className="res-time-val">{avgResTime.display}</span>
                <p className="res-time-note">{avgResTime.note}</p>
              </>
            ) : (
              <>
                <div className="res-time-unavailable">
                  <span className="unavailable-badge">Telemetry Unavailable</span>
                  <p className="unavailable-note">{avgResTime.note}</p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Recurring Incident Patterns */}
        <div className="insight-box">
          <div className="insight-box-header">
            <span className="insight-icon">🔁</span>
            <h5>Recurring Patterns</h5>
          </div>
          {recurringPatterns.length === 0 ? (
            <div className="pattern-single-state">
              <span className="pattern-badge-info">Pattern Engine Active</span>
              <p className="pattern-desc">
                Requires 2+ correlated incidents to confirm a recurring operational pattern.
              </p>
            </div>
          ) : (
            <div className="patterns-list">
              {recurringPatterns.map((pat) => (
                <div key={pat.pattern} className="pattern-item">
                  <div className="pattern-header">
                    <strong>{pat.pattern}</strong>
                    <span className="pattern-count-badge">{pat.count} events</span>
                  </div>
                  <p className="pattern-desc-text">{pat.description}</p>
                  <div className="pattern-services-tags">
                    {pat.services.map((svc) => (
                      <span key={svc} className="tag-tiny">{svc}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 4. Memory Intelligence (Hindsight Bank) */}
      <div className="memory-intelligence-section mt-4 mb-4">
        <div className="memory-intel-card">
          <div className="memory-intel-header">
            <div className="memory-intel-title-group">
              <div className="memory-badge-row">
                <span className="spotlight-badge">🧠 Hindsight Memory Engine</span>
                <span className={`engine-status-badge ${memoryStatus.status === 'online' ? 'status-online' : 'status-offline'}`}>
                  ● {memoryStatus.mode}
                </span>
              </div>
              <h3>Persistent Institutional Knowledge Bank</h3>
              <p>
                Target Bank: <code>{memoryStatus.bank_id}</code> · Human Verification Gate:{' '}
                <strong>Enforced</strong> (Speculative guesses are barred from persistent memory)
              </p>
            </div>
            {onNavigateMemory && (
              <button
                type="button"
                className="secondary-btn memory-explorer-btn"
                onClick={onNavigateMemory}
              >
                Explore Memory Bank →
              </button>
            )}
          </div>

          <div className="memory-intel-stats-row">
            <div className="memory-stat-box">
              <span className="memory-stat-number">{memories}</span>
              <span className="memory-stat-title">Total Retained Incidents</span>
              <span className="memory-stat-desc">Permanent diagnostic records</span>
            </div>
            <div className="memory-stat-box">
              <span className="memory-stat-number">{memoryIntel.verified_resolutions || resolved}</span>
              <span className="memory-stat-title">Verified Resolutions</span>
              <span className="memory-stat-desc">Confirmed by human SREs</span>
            </div>
            <div className="memory-stat-box">
              <span className="memory-stat-number">{frequentlyRecalled.length}</span>
              <span className="memory-stat-title">Recalled Incident Citations</span>
              <span className="memory-stat-desc">Past solutions reused in diagnosis</span>
            </div>
          </div>

          {/* Recall Statistics / Citation Details */}
          <div className="memory-recall-footer">
            <span className="recall-footer-label">Memory Recall Telemetry:</span>
            {hasRecallStats && frequentlyRecalled.length > 0 ? (
              <div className="recalled-pills-list">
                {frequentlyRecalled.map((item) => (
                  <span key={item.incident_id} className="recalled-pill">
                    📎 {item.incident_id} ({item.recall_count}x citation{item.recall_count !== 1 ? 's' : ''})
                  </span>
                ))}
              </div>
            ) : (
              <span className="recall-note-text">
                {memoryIntel.recall_note || 'Active: Historical memories are recalled dynamically when new incidents exhibit matching symptoms.'}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 4b. Response Action Telemetry (Part 4) */}
      {actionsSummary && actionsSummary.total_actions > 0 && (
        <div className="response-telemetry-banner mb-4">
          <div className="response-telemetry-card">
            <div className="response-telemetry-left">
              <div className="telemetry-badge-row">
                <span className="spotlight-badge">⚡ Response Workflow Telemetry</span>
                <span className="telemetry-summary-tag">
                  {actionsSummary.completed_actions} of {actionsSummary.total_actions} tasks finished
                </span>
              </div>
              <h4>Guided Incident Action Execution</h4>
              <p>
                Engineer-driven diagnostic validations and remediations across active incidents.
                {actionsSummary.blocked_actions > 0 && (
                  <span className="blocked-alert-inline">
                    {' '}⚠️ <strong>{actionsSummary.blocked_actions} task(s)</strong> currently flagged as blocked.
                  </span>
                )}
              </p>
              <div className="telemetry-progress-track">
                <div
                  className="telemetry-progress-fill"
                  style={{ width: `${actionsSummary.completion_rate || 0}%` }}
                />
              </div>
            </div>

            <div className="response-telemetry-stats">
              <div className="res-stat-box stat-comp">
                <span className="res-stat-num">{actionsSummary.completed_actions}</span>
                <span className="res-stat-lbl">Completed</span>
              </div>
              <div className="res-stat-box stat-prog">
                <span className="res-stat-num">{actionsSummary.in_progress_actions}</span>
                <span className="res-stat-lbl">In Progress</span>
              </div>
              <div className="res-stat-box stat-pend">
                <span className="res-stat-num">{actionsSummary.pending_actions}</span>
                <span className="res-stat-lbl">Pending</span>
              </div>
              {actionsSummary.blocked_actions > 0 && (
                <div className="res-stat-box stat-block">
                  <span className="res-stat-num">{actionsSummary.blocked_actions}</span>
                  <span className="res-stat-lbl">Blocked</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 5. Recent Incidents Telemetry */}
      <section className="dashboard-section">
        <div className="section-header-row">
          <div className="section-title-group">
            <h3>Recent Incidents Telemetry</h3>
            <span className="section-note">Operational stream of inspected failure events</span>
          </div>

          <div className="filter-and-view-group">
            {/* Filter Tabs */}
            <div className="filter-tabs-pills">
              <button
                type="button"
                className={`filter-tab-btn ${incidentFilter === 'all' ? 'active' : ''}`}
                onClick={() => setIncidentFilter('all')}
              >
                All ({recentIncidents.length})
              </button>
              <button
                type="button"
                className={`filter-tab-btn ${incidentFilter === 'critical' ? 'active' : ''}`}
                onClick={() => setIncidentFilter('critical')}
              >
                Critical ({criticalCount})
              </button>
              <button
                type="button"
                className={`filter-tab-btn ${incidentFilter === 'active' ? 'active' : ''}`}
                onClick={() => setIncidentFilter('active')}
              >
                Active ({openCount})
              </button>
              <button
                type="button"
                className={`filter-tab-btn ${incidentFilter === 'resolved' ? 'active' : ''}`}
                onClick={() => setIncidentFilter('resolved')}
              >
                Resolved ({resolved})
              </button>
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
        </div>

        {filteredIncidents.length === 0 ? (
          <div className="empty-card">
            {recentIncidents.length === 0 ? (
              <>
                <p>No incidents recorded in the repository yet.</p>
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={onNavigateNew}
                >
                  Investigate Scenario A (Orders API 500)
                </button>
              </>
            ) : (
              <p>No incidents match the selected filter &quot;{incidentFilter}&quot;.</p>
            )}
          </div>
        ) : (
          <div className="incidents-grid">
            {filteredIncidents.map((incident) => (
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
