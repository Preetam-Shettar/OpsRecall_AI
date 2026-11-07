import React, { useState } from 'react';
import IncidentForm from '../components/IncidentForm';
import LoadingState from '../components/LoadingState';
import AnalysisPanel from '../components/AnalysisPanel';
import MemoryMatchCard from '../components/MemoryMatchCard';
import ResolutionForm from '../components/ResolutionForm';

export default function NewIncident({
  onSubmitIncident,
  onSaveResolution,
  isSubmitting,
  submittedIncident,
}) {
  const [error, setError] = useState('');

  async function handleFormSubmit(formData) {
    setError('');
    try {
      await onSubmitIncident(formData);
    } catch (err) {
      setError(err.message || 'Submission failed');
    }
  }

  return (
    <div className="page new-incident-page">
      <div className="page-header">
        <div>
          <h2>Investigate &amp; Diagnose Incident</h2>
          <p className="page-subtitle">
            Submit logs and context. OpsRecall will query Hindsight memory and analyze root-cause clues.
          </p>
        </div>
      </div>

      {error && <div className="page-error-alert">{error}</div>}

      <div className="new-incident-layout">
        {/* Left Column: Form */}
        <div className="layout-col form-col">
          <IncidentForm
            onSubmit={handleFormSubmit}
            isSubmitting={isSubmitting}
          />
        </div>

        {/* Right Column: Dynamic Diagnosis & Memory Results */}
        <div className="layout-col results-col">
          {isSubmitting ? (
            <LoadingState message="Analyzing logs, evaluating operational signals, and checking Hindsight memory..." />
          ) : submittedIncident ? (
            <div className="diagnosis-flow">
              {/* Recalled Memory Box (Visible Recall!) */}
              <MemoryMatchCard memories={submittedIncident.related_memories || submittedIncident.analysis?.related_memory_insights || []} />

              {/* Analysis Diagnosis Panel */}
              <AnalysisPanel analysis={submittedIncident.analysis} />

              {/* Resolution Form (Allows immediate retain to memory) */}
              <ResolutionForm
                incident={submittedIncident}
                onSaveResolution={onSaveResolution}
              />
            </div>
          ) : (
            <div className="empty-results-box">
              <span className="empty-bulb">💡</span>
              <h4>Awaiting Incident Submission</h4>
              <p>
                Click one of the Quick Demo Scenarios on the left or paste your own logs to generate an AI diagnosis informed by persistent memory.
              </p>
              <div className="demo-tip-card">
                <strong>Tip for Testing Memory:</strong>
                <ol>
                  <li>Submit <strong>Scenario A</strong> (Orders API 500)</li>
                  <li>Click <strong>Fill Demo Resolution</strong> and save it (retains in Hindsight)</li>
                  <li>Submit <strong>Scenario B</strong> (Checkout API Timeout)</li>
                  <li>Watch Scenario A appear in <strong>Related Past Incidents</strong> to inform the diagnosis!</li>
                </ol>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
