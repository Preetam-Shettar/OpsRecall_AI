import React, { useState } from 'react';

const SCENARIO_A = {
  title: 'Orders API returns HTTP 500 after deployment',
  service: 'orders-api',
  environment: 'staging',
  description: 'Requests began failing after the latest deployment release. Latency spiked sharply.',
  deployment_context: 'Release 1.4.2 (scaled worker threads)',
  logs: `2026-11-07 10:12:01 ERROR orders-api
Database connection acquisition timed out after 30 seconds.
2026-11-07 10:12:02 ERROR orders-api
Request failed: GET /orders - ConnectionPoolTimeoutException
2026-11-07 10:12:03 WARN database-pool
Active connections reached configured maximum (10/10). Queue depth: 42.`,
};

const SCENARIO_B = {
  title: 'Checkout API timing out after scaling workers',
  service: 'checkout-api',
  environment: 'production',
  description: 'Worker concurrency was increased and checkout orders began timing out on DB connection acquisition.',
  deployment_context: 'Scaled worker pool from 4 to 16 workers',
  logs: `2026-11-08 09:30:10 ERROR checkout-api
Timeout waiting for database connection from pool.
2026-11-08 09:30:11 WARN database-pool
Connection pool utilization: 100% (pool size: 10).
2026-11-08 09:30:12 ERROR checkout-api
Transaction rollback: could not acquire db lease within timeout.`,
};

export default function IncidentForm({ onSubmit, isSubmitting }) {
  const [formData, setFormData] = useState({
    title: '',
    service: '',
    environment: 'staging',
    description: '',
    deployment_context: '',
    logs: '',
  });

  function loadScenario(scenario) {
    setFormData(scenario);
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!formData.title || !formData.service || !formData.description) return;
    onSubmit(formData);
  }

  return (
    <div className="incident-form-card">
      <div className="form-header">
        <div className="form-header-title">
          <h3>Submit Incident for AI Investigation</h3>
          <p>OpsRecall AI will inspect logs, sanitize secrets, recall past incidents from Hindsight, and generate a cautious diagnosis.</p>
        </div>

        {/* Demo Scenario Buttons */}
        <div className="scenario-buttons-row">
          <span className="scenario-label">Quick Demo Scenarios:</span>
          <button
            type="button"
            className="scenario-btn scenario-a"
            onClick={() => loadScenario(SCENARIO_A)}
          >
            Scenario A (Orders API 500)
          </button>
          <button
            type="button"
            className="scenario-btn scenario-b"
            onClick={() => loadScenario(SCENARIO_B)}
          >
            Scenario B (Checkout Timeout)
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="incident-form">
        <div className="form-group">
          <label htmlFor="title">Incident Title *</label>
          <input
            id="title"
            type="text"
            required
            placeholder="e.g. Orders API returning 500 errors after release"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          />
        </div>

        <div className="form-row-2">
          <div className="form-group">
            <label htmlFor="service">Affected Service / Component *</label>
            <input
              id="service"
              type="text"
              required
              placeholder="e.g. orders-api, checkout-service"
              value={formData.service}
              onChange={(e) => setFormData({ ...formData, service: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label htmlFor="environment">Environment</label>
            <select
              id="environment"
              value={formData.environment}
              onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
            >
              <option value="production">Production</option>
              <option value="staging">Staging</option>
              <option value="development">Development</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="description">Observed Problem Description *</label>
          <textarea
            id="description"
            rows={3}
            required
            placeholder="Describe what occurred, how the failure was detected, and symptoms..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label htmlFor="deployment_context">Deployment / Change Context (Optional)</label>
          <input
            id="deployment_context"
            type="text"
            placeholder="e.g. Deployed v1.4.2, changed worker threads, rotated credentials"
            value={formData.deployment_context}
            onChange={(e) => setFormData({ ...formData, deployment_context: e.target.value })}
          />
        </div>

        <div className="form-group">
          <div className="label-with-tip">
            <label htmlFor="logs">Error Logs / Stack Traces</label>
            <span className="sanitizer-tip">🔒 Sensitive tokens, keys, and passwords will be automatically redacted</span>
          </div>
          <textarea
            id="logs"
            rows={7}
            className="code-textarea"
            placeholder="Paste application logs, stack traces, or console output here..."
            value={formData.logs}
            onChange={(e) => setFormData({ ...formData, logs: e.target.value })}
          />
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="submit-btn"
            disabled={isSubmitting || !formData.title || !formData.service}
          >
            {isSubmitting ? 'Analyzing Incident & Recalling Memory...' : 'Investigate Incident with AI'}
          </button>
        </div>
      </form>
    </div>
  );
}
