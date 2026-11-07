import React, { useState } from 'react';
import { api } from '../services/api';

export default function MemoryExplorer() {
  const [query, setQuery] = useState('database connection pool timeout');
  const [budget, setBudget] = useState('mid');
  const [activeTab, setActiveTab] = useState('recall'); // 'recall' or 'reflect'
  const [loading, setLoading] = useState(false);
  const [recallResults, setRecallResults] = useState(null);
  const [reflectResult, setReflectResult] = useState(null);
  const [error, setError] = useState('');

  async function handleRecall() {
    if (!query) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.recallMemory(query, budget);
      setRecallResults(data);
    } catch (err) {
      setError(err.message || 'Recall failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleReflect() {
    if (!query) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.reflectMemory(query, budget);
      setReflectResult(data);
    } catch (err) {
      setError(err.message || 'Reflect failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page memory-explorer-page">
      <div className="page-header">
        <div>
          <h2>Hindsight Memory Bank Explorer</h2>
          <p className="page-subtitle">
            Inspect persistent memories, test semantic recall queries, and trigger cross-incident reflection synthesis.
          </p>
        </div>
      </div>

      <div className="memory-explorer-card">
        <div className="explorer-query-box">
          <div className="form-group">
            <label htmlFor="mem-query">Natural Language Incident Query</label>
            <input
              id="mem-query"
              type="text"
              placeholder="e.g. database connection acquisition timeout orders-api"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="explorer-controls">
            <div className="budget-selector">
              <label htmlFor="budget-select">Hindsight Search Budget:</label>
              <select
                id="budget-select"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
              >
                <option value="low">Low (Fast)</option>
                <option value="mid">Mid (Balanced)</option>
                <option value="high">High (Deep)</option>
              </select>
            </div>

            <div className="action-buttons-group">
              <button
                type="button"
                className={`action-btn ${activeTab === 'recall' ? 'active' : ''}`}
                disabled={loading}
                onClick={() => {
                  setActiveTab('recall');
                  handleRecall();
                }}
              >
                {loading && activeTab === 'recall' ? 'Recalling...' : '⚡ Test Hindsight Recall'}
              </button>
              <button
                type="button"
                className={`action-btn ${activeTab === 'reflect' ? 'active' : ''}`}
                disabled={loading}
                onClick={() => {
                  setActiveTab('reflect');
                  handleReflect();
                }}
              >
                {loading && activeTab === 'reflect' ? 'Reflecting...' : '🔮 Synthesize Reflection'}
              </button>
            </div>
          </div>
        </div>

        {error && <div className="page-error-alert">{error}</div>}

        {/* Results Area */}
        <div className="explorer-results">
          {activeTab === 'recall' && (
            <div className="recall-results-view">
              <div className="results-header">
                <h4>Recall Matches ({recallResults?.results?.length || 0})</h4>
                {recallResults?.bank_id && (
                  <span className="bank-pill">Bank: {recallResults.bank_id}</span>
                )}
              </div>

              {!recallResults ? (
                <p className="hint-text">Click "Test Hindsight Recall" to retrieve historical incidents matching the query.</p>
              ) : recallResults.results?.length === 0 ? (
                <p className="hint-text">No matching memories found for this query in the bank.</p>
              ) : (
                <div className="recalled-cards-list">
                  {recallResults.results.map((item, idx) => (
                    <div key={idx} className="recalled-item-card">
                      <div className="card-top-row">
                        <span className="memory-id-badge">{item.incident_id || `Mem #${idx + 1}`}</span>
                        {item.service && <span className="service-tag">{item.service}</span>}
                        {item.source && <span className="source-tag">{item.source}</span>}
                      </div>
                      <pre className="recalled-content-pre">{item.content}</pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'reflect' && (
            <div className="reflect-results-view">
              <div className="results-header">
                <h4>Hindsight Cross-Incident Reflection</h4>
                {reflectResult?.bank_id && (
                  <span className="bank-pill">Bank: {reflectResult.bank_id}</span>
                )}
              </div>

              {!reflectResult ? (
                <p className="hint-text">Click "Synthesize Reflection" to generate a cross-incident pattern analysis from memory.</p>
              ) : (
                <div className="reflection-output-box">
                  <div className="reflection-icon">🔮</div>
                  <div className="reflection-text">
                    <p>{reflectResult.summary}</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
