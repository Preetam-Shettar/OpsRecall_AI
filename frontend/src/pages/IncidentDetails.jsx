import React, { useState } from 'react';
import ActionPlanBoard from '../components/ActionPlanBoard';
import AnalysisPanel from '../components/AnalysisPanel';
import IncidentTimeline from '../components/IncidentTimeline';
import MemoryMatchCard from '../components/MemoryMatchCard';
import ResolutionForm from '../components/ResolutionForm';
import { formatDate, formatStatus } from '../utils/formatters';

export default function IncidentDetails({ incident, onSaveResolution, onBack }) {
  const [activeTab, setActiveTab] = useState('analysis'); // 'analysis', 'response', 'logs', 'resolution'
  const [responseSubTab, setResponseSubTab] = useState('actions'); // 'actions', 'timeline'
  const [compiledFindings, setCompiledFindings] = useState('');

  if (!incident) {
    return (
      <div className="page incident-details-page">
        <p>No incident selected.</p>
        <button type="button" className="secondary-btn" onClick={onBack}>
          ← Back to History
        </button>
      </div>
    );
  }

  const statusInfo = formatStatus(incident.status);
  const memories = incident.related_memories || incident.analysis?.related_memory_insights || [];

  function handleProceedToResolution(findingsText) {
    setCompiledFindings(findingsText);
    setActiveTab('resolution');
  }

  return (
    <div className="page incident-details-page">
      <div className="page-header details-header">
        <div>
          <button type="button" className="back-link" onClick={onBack}>
            ← Back to History
          </button>
          <div className="title-with-badge">
            <h2>{incident.title}</h2>
            <span className={`status-pill ${statusInfo.badgeClass}`}>
              {statusInfo.label}
            </span>
          </div>
          <div className="details-submeta">
            <span className="submeta-item"><strong>ID:</strong> {incident.id}</span>
            <span className="submeta-divider">•</span>
            <span className="submeta-item"><strong>Service:</strong> {incident.service}</span>
            <span className="submeta-divider">•</span>
            <span className="submeta-item"><strong>Environment:</strong> {incident.environment}</span>
            <span className="submeta-divider">•</span>
            <span className="submeta-item"><strong>Detected:</strong> {formatDate(incident.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs-nav">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'analysis' ? 'active' : ''}`}
          onClick={() => setActiveTab('analysis')}
        >
          🔍 AI Diagnosis &amp; Memory
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'response' ? 'active' : ''}`}
          onClick={() => setActiveTab('response')}
        >
          ⚡ Guided Response &amp; Actions
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          📄 Evidence &amp; Sanitized Logs
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'resolution' ? 'active' : ''}`}
          onClick={() => setActiveTab('resolution')}
        >
          ✅ Verified Resolution {incident.resolution ? '(Recorded)' : ''}
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'analysis' && (
          <div className="details-analysis-tab">
            {/* Memory Recall Context */}
            <MemoryMatchCard memories={memories} />

            {/* Analysis details */}
            <AnalysisPanel analysis={incident.analysis} />
          </div>
        )}

        {activeTab === 'response' && (
          <div className="details-response-tab">
            {/* Sub-view switcher for response workspace */}
            <div className="response-subnav">
              <button
                type="button"
                className={`response-subnav-btn ${responseSubTab === 'actions' ? 'active' : ''}`}
                onClick={() => setResponseSubTab('actions')}
              >
                📋 Action Plan &amp; Diagnostic Tasks
              </button>
              <button
                type="button"
                className={`response-subnav-btn ${responseSubTab === 'timeline' ? 'active' : ''}`}
                onClick={() => setResponseSubTab('timeline')}
              >
                ⏱️ Chronological Timeline &amp; Audit Trail
              </button>
            </div>

            {responseSubTab === 'actions' && (
              <ActionPlanBoard
                incident={incident}
                onProceedToResolution={handleProceedToResolution}
              />
            )}

            {responseSubTab === 'timeline' && (
              <IncidentTimeline incidentId={incident.id} />
            )}
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="details-logs-tab">
            <div className="panel log-box-panel">
              <div className="log-panel-header">
                <h4>Sanitized Log Evidence</h4>
                <span className="sanitizer-badge">🛡️ Credentials &amp; Secrets Redacted</span>
              </div>
              <pre className="log-viewer">
                {incident.sanitized_logs || incident.logs || 'No logs provided.'}
              </pre>
            </div>

            {incident.metadata?.deployment_context && (
              <div className="panel meta-detail-panel">
                <h4>Deployment / Change Context</h4>
                <p>{incident.metadata.deployment_context}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'resolution' && (
          <div className="details-resolution-tab">
            <ResolutionForm
              incident={incident}
              onSaveResolution={onSaveResolution}
              initialResolutionNotes={compiledFindings}
            />
          </div>
        )}
      </div>
    </div>
  );
}
