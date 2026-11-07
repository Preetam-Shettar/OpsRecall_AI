import React, { useState } from 'react';

export default function ResolutionForm({ incident, onSaveResolution }) {
  const [rootCause, setRootCause] = useState(
    incident?.resolution?.root_cause || ''
  );
  const [resolutionSteps, setResolutionSteps] = useState(
    incident?.resolution?.resolution || ''
  );
  const [outcome, setOutcome] = useState(incident?.resolution?.outcome || 'resolved');
  const [engineer, setEngineer] = useState(incident?.resolution?.engineer || 'Site Reliability Engineer');
  const [verified, setVerified] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState('');

  // Pre-fill helper for demo scenario
  function fillDemoFix() {
    setRootCause('Database connection pool limit (10) was too low for the new worker thread count (16).');
    setResolutionSteps('Increased pool_size to 40 in config, adjusted timeout to 45s, and restarted the service.');
    setOutcome('resolved');
    setVerified(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!rootCause || !resolutionSteps) return;

    setSaving(true);
    setError('');
    setSavedSuccess(false);

    try {
      await onSaveResolution({
        root_cause: rootCause,
        resolution: resolutionSteps,
        outcome,
        engineer,
        verified,
      });
      setSavedSuccess(true);
    } catch (err) {
      setError(err.message || 'Failed to save resolution');
    } finally {
      setSaving(false);
    }
  }

  const isAlreadyResolved = incident?.status === 'resolved' || incident?.status === 'mitigated';

  return (
    <div className="resolution-form-card">
      <div className="resolution-header">
        <div className="resolution-title-area">
          <h4>Resolution Feedback &amp; Hindsight Learning</h4>
          <p>
            Recording a verified outcome teaches the AI agent. Only engineer-confirmed root causes and resolutions are retained into persistent memory.
          </p>
        </div>
        {!isAlreadyResolved && (
          <button type="button" className="demo-fill-btn" onClick={fillDemoFix}>
            Fill Demo Resolution
          </button>
        )}
      </div>

      {savedSuccess && (
        <div className="resolution-success-alert">
          <span className="success-icon">✓</span>
          <div>
            <strong>Resolution confirmed &amp; retained in Hindsight!</strong>
            <p>This incident's verified outcome is now part of the persistent memory bank and will automatically inform future similar incidents.</p>
          </div>
        </div>
      )}

      {error && <div className="resolution-error-alert">{error}</div>}

      <form onSubmit={handleSubmit} className="resolution-form">
        <div className="form-group">
          <label htmlFor="root_cause">Confirmed Root Cause *</label>
          <input
            id="root_cause"
            type="text"
            required
            placeholder="e.g. Database connection pool exhausted due to worker concurrency mismatch"
            value={rootCause}
            onChange={(e) => setRootCause(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label htmlFor="resolution_steps">Verified Resolution Steps *</label>
          <textarea
            id="resolution_steps"
            rows={3}
            required
            placeholder="Explain what steps successfully mitigated or fixed the issue..."
            value={resolutionSteps}
            onChange={(e) => setResolutionSteps(e.target.value)}
          />
        </div>

        <div className="form-row-2">
          <div className="form-group">
            <label htmlFor="outcome">Incident Outcome</label>
            <select
              id="outcome"
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
            >
              <option value="resolved">Resolved</option>
              <option value="mitigated">Mitigated</option>
              <option value="unresolved">Unresolved</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="engineer">Investigating Engineer</label>
            <input
              id="engineer"
              type="text"
              placeholder="e.g. Alice / On-Call SRE"
              value={engineer}
              onChange={(e) => setEngineer(e.target.value)}
            />
          </div>
        </div>

        <div className="form-checkbox-group">
          <input
            type="checkbox"
            id="verified"
            checked={verified}
            onChange={(e) => setVerified(e.target.checked)}
          />
          <label htmlFor="verified">
            I confirm that this root cause and resolution were verified by an engineer (required for persistent Hindsight retain)
          </label>
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="save-resolution-btn"
            disabled={saving || !rootCause || !resolutionSteps}
          >
            {saving ? 'Retaining to Hindsight...' : isAlreadyResolved ? 'Update & Retain Learning' : 'Save Verified Resolution & Retain in Hindsight'}
          </button>
        </div>
      </form>
    </div>
  );
}
