import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { formatDate, formatSeverity } from '../utils/formatters';

export default function MemoryExplorer() {
  const [activeMainTab, setActiveMainTab] = useState('catalog'); // 'catalog' or 'lab'

  // Catalog State
  const [memories, setMemories] = useState([]);
  const [totalMemories, setTotalMemories] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [serviceFilter, setServiceFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [envFilter, setEnvFilter] = useState('');
  const [verifiedFilter, setVerifiedFilter] = useState('true'); // 'true', 'false', 'all'
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState('');

  // Selected Memory Detail State (Inspection Drawer)
  const [selectedMemory, setSelectedMemory] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');

  // Lab State (Semantic Recall & Reflect)
  const [query, setQuery] = useState('database connection pool timeout');
  const [budget, setBudget] = useState('mid');
  const [labTab, setLabTab] = useState('recall'); // 'recall' or 'reflect'
  const [labLoading, setLabLoading] = useState(false);
  const [recallResults, setRecallResults] = useState(null);
  const [reflectResult, setReflectResult] = useState(null);
  const [labError, setLabError] = useState('');

  // Fetch catalog memories when filters/pagination change
  useEffect(() => {
    if (activeMainTab === 'catalog') {
      loadCatalogMemories();
    }
  }, [page, pageSize, serviceFilter, severityFilter, envFilter, verifiedFilter, activeMainTab]);

  // Debounced search
  useEffect(() => {
    if (activeMainTab !== 'catalog') return;
    const timer = setTimeout(() => {
      setPage(1);
      loadCatalogMemories();
    }, 350);
    return () => clearTimeout(timer);
  }, [search]);

  async function loadCatalogMemories() {
    setCatalogLoading(true);
    setCatalogError('');
    try {
      const params = {
        page,
        pageSize,
      };
      if (search.trim()) params.search = search.trim();
      if (serviceFilter) params.service = serviceFilter;
      if (severityFilter) params.severity = severityFilter;
      if (envFilter) params.environment = envFilter;
      if (verifiedFilter === 'true') params.verified = true;
      else if (verifiedFilter === 'false') params.verified = false;
      else if (verifiedFilter === 'all') params.verified = null;

      const data = await api.listMemories(params);
      setMemories(data.items || []);
      setTotalMemories(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      setCatalogError(err.message || 'Failed to load memory catalog.');
    } finally {
      setCatalogLoading(false);
    }
  }

  async function handleOpenDetail(memoryId) {
    setDetailLoading(true);
    setDetailError('');
    setSelectedMemory(null);
    try {
      const detail = await api.getMemoryDetail(memoryId);
      setSelectedMemory(detail);
    } catch (err) {
      setDetailError(err.message || 'Failed to load memory details.');
    } finally {
      setDetailLoading(false);
    }
  }

  function handleCloseDetail() {
    setSelectedMemory(null);
  }

  async function handleRecall() {
    if (!query) return;
    setLabLoading(true);
    setLabError('');
    try {
      const data = await api.recallMemory(query, budget);
      setRecallResults(data);
    } catch (err) {
      setLabError(err.message || 'Recall failed');
    } finally {
      setLabLoading(false);
    }
  }

  async function handleReflect() {
    if (!query) return;
    setLabLoading(true);
    setLabError('');
    try {
      const data = await api.reflectMemory(query, budget);
      setReflectResult(data);
    } catch (err) {
      setLabError(err.message || 'Reflect failed');
    } finally {
      setLabLoading(false);
    }
  }

  return (
    <div className="page memory-explorer-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h2>Incident Memory Explorer</h2>
          <p className="page-subtitle">
            Browse, search, inspect, and analyze persistent institutional knowledge retained across incident triage cycles.
          </p>
        </div>

        {/* Primary Tab Switcher */}
        <div className="memory-nav-tabs">
          <button
            type="button"
            className={`memory-nav-btn ${activeMainTab === 'catalog' ? 'active' : ''}`}
            onClick={() => setActiveMainTab('catalog')}
          >
            🏛️ Memory Catalog ({totalMemories})
          </button>
          <button
            type="button"
            className={`memory-nav-btn ${activeMainTab === 'lab' ? 'active' : ''}`}
            onClick={() => setActiveMainTab('lab')}
          >
            🧪 Recall &amp; Reflect Lab
          </button>
        </div>
      </div>

      {/* ============================================================== */}
      {/* TAB 1: INSTITUTIONAL MEMORY CATALOG                            */}
      {/* ============================================================== */}
      {activeMainTab === 'catalog' && (
        <div className="memory-catalog-container">
          {/* Controls Bar: Search & Filters */}
          <div className="catalog-toolbar-card">
            <div className="catalog-search-row">
              <div className="catalog-search-input-wrapper">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  className="catalog-search-input"
                  placeholder="Search by incident ID, service, root cause keywords, or resolution..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                {search && (
                  <button
                    type="button"
                    className="clear-search-btn"
                    onClick={() => setSearch('')}
                  >
                    ✕
                  </button>
                )}
              </div>

              <div className="verification-filter-group">
                <label htmlFor="verified-select">Trust Gate:</label>
                <select
                  id="verified-select"
                  className="catalog-select"
                  value={verifiedFilter}
                  onChange={(e) => {
                    setVerifiedFilter(e.target.value);
                    setPage(1);
                  }}
                >
                  <option value="true">✓ Verified Only (Trusted Catalog)</option>
                  <option value="all">All Records (Verified &amp; Unverified)</option>
                  <option value="false">⚠️ Unverified Records Only</option>
                </select>
              </div>
            </div>

            {/* Filter Pills Row */}
            <div className="catalog-filters-row">
              <div className="filter-pill-item">
                <span className="filter-pill-label">Service:</span>
                <select
                  className="catalog-filter-select"
                  value={serviceFilter}
                  onChange={(e) => {
                    setServiceFilter(e.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All Services</option>
                  <option value="orders-api">orders-api</option>
                  <option value="checkout-api">checkout-api</option>
                  <option value="checkout-service">checkout-service</option>
                  <option value="inventory-service">inventory-service</option>
                  <option value="auth-service">auth-service</option>
                </select>
              </div>

              <div className="filter-pill-item">
                <span className="filter-pill-label">Severity:</span>
                <select
                  className="catalog-filter-select"
                  value={severityFilter}
                  onChange={(e) => {
                    setSeverityFilter(e.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <div className="filter-pill-item">
                <span className="filter-pill-label">Environment:</span>
                <select
                  className="catalog-filter-select"
                  value={envFilter}
                  onChange={(e) => {
                    setEnvFilter(e.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All Environments</option>
                  <option value="production">Production</option>
                  <option value="staging">Staging</option>
                  <option value="development">Development</option>
                </select>
              </div>

              {(search || serviceFilter || severityFilter || envFilter || verifiedFilter !== 'true') && (
                <button
                  type="button"
                  className="reset-filters-btn"
                  onClick={() => {
                    setSearch('');
                    setServiceFilter('');
                    setSeverityFilter('');
                    setEnvFilter('');
                    setVerifiedFilter('true');
                    setPage(1);
                  }}
                >
                  Reset Filters
                </button>
              )}
            </div>
          </div>

          {/* Verification Guardrail Notice */}
          {verifiedFilter === 'true' && (
            <div className="verification-guardrail-banner">
              <span className="shield-icon">🛡️</span>
              <p>
                <strong>Human Verification Gate Active:</strong> Showing only engineer-confirmed resolutions. Unverified chatbot hypotheses are quarantined to prevent hallucination propagation.
              </p>
            </div>
          )}

          {verifiedFilter === 'false' && (
            <div className="verification-warning-banner">
              <span className="shield-icon">⚠️</span>
              <p>
                <strong>Unverified Records:</strong> These resolutions have not been signed off by a human engineer. They are excluded from automated triage recall.
              </p>
            </div>
          )}

          {catalogError && <div className="page-error-alert">{catalogError}</div>}

          {/* Memory Cards Grid */}
          {catalogLoading ? (
            <div className="catalog-loading-state">
              <div className="spinner"></div>
              <p>Loading persistent memories from repository...</p>
            </div>
          ) : memories.length === 0 ? (
            <div className="empty-catalog-card">
              <div className="empty-catalog-icon">🧠</div>
              <h4>No Memory Records Found</h4>
              <p>
                {search || serviceFilter || severityFilter || envFilter
                  ? 'No memories matched the selected search criteria and filters.'
                  : 'No verified resolutions have been retained in the persistent memory bank yet.'}
              </p>
              {(search || serviceFilter || severityFilter || envFilter || verifiedFilter !== 'true') && (
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() => {
                    setSearch('');
                    setServiceFilter('');
                    setSeverityFilter('');
                    setEnvFilter('');
                    setVerifiedFilter('true');
                    setPage(1);
                  }}
                >
                  Clear Filters
                </button>
              )}
            </div>
          ) : (
            <div className="memory-cards-grid">
              {memories.map((mem) => {
                const sevInfo = formatSeverity(mem.severity);
                return (
                  <div
                    key={mem.id}
                    className={`memory-catalog-card ${!mem.verified ? 'card-unverified' : ''}`}
                    onClick={() => handleOpenDetail(mem.id)}
                    role="button"
                    tabIndex={0}
                  >
                    <div className="mem-card-header">
                      <span className="mem-inc-id">{mem.incident_id}</span>
                      <div className="mem-header-badges">
                        {mem.verified ? (
                          <span className="badge-verified-pill">✓ Confirmed Fix</span>
                        ) : (
                          <span className="badge-unverified-pill">⚠️ Unverified</span>
                        )}
                        <span className={`status-pill ${sevInfo.badgeClass}`}>
                          {sevInfo.label}
                        </span>
                      </div>
                    </div>

                    <h4 className="mem-card-title">{mem.title}</h4>

                    <div className="mem-card-cause-box">
                      <span className="mem-cause-label">Confirmed Root Cause:</span>
                      <p className="mem-cause-text">{mem.root_cause}</p>
                    </div>

                    <div className="mem-card-meta-row">
                      <span className="meta-tag service-tag">{mem.service}</span>
                      <span className="meta-tag env-tag">{mem.environment}</span>
                      <span className="meta-tag provider-tag">
                        ● {mem.storage_provider}
                      </span>
                    </div>

                    <div className="mem-card-footer">
                      <div className="mem-engineer-attribution">
                        {mem.engineer ? (
                          <span>Verified by <strong>{mem.engineer}</strong></span>
                        ) : (
                          <span>System Record</span>
                        )}
                        <span className="mem-timestamp"> · {formatDate(mem.created_at)}</span>
                      </div>
                      <div className="mem-citations-badge" title="Number of subsequent incidents citing this memory">
                        📎 {mem.recall_count} citation{mem.recall_count !== 1 ? 's' : ''}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Pagination Controls */}
          {totalMemories > 0 && (
            <div className="catalog-pagination-row">
              <div className="pagination-info">
                Showing{' '}
                <strong>
                  {Math.min((page - 1) * pageSize + 1, totalMemories)} -{' '}
                  {Math.min(page * pageSize, totalMemories)}
                </strong>{' '}
                of <strong>{totalMemories}</strong> memory records
              </div>

              <div className="pagination-controls-group">
                <button
                  type="button"
                  className="page-nav-btn"
                  disabled={page <= 1 || catalogLoading}
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                >
                  ← Previous
                </button>
                <span className="page-number-indicator">
                  Page <strong>{page}</strong> of <strong>{totalPages}</strong>
                </span>
                <button
                  type="button"
                  className="page-nav-btn"
                  disabled={page >= totalPages || catalogLoading}
                  onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                >
                  Next →
                </button>

                <div className="page-size-selector">
                  <label htmlFor="page-size-select">Per page:</label>
                  <select
                    id="page-size-select"
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setPage(1);
                    }}
                  >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 2: SEMANTIC RECALL & REFLECT LAB (PRESERVED)               */}
      {/* ============================================================== */}
      {activeMainTab === 'lab' && (
        <div className="memory-lab-container">
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
                    className={`action-btn ${labTab === 'recall' ? 'active' : ''}`}
                    disabled={labLoading}
                    onClick={() => {
                      setLabTab('recall');
                      handleRecall();
                    }}
                  >
                    {labLoading && labTab === 'recall' ? 'Recalling...' : '⚡ Test Hindsight Recall'}
                  </button>
                  <button
                    type="button"
                    className={`action-btn ${labTab === 'reflect' ? 'active' : ''}`}
                    disabled={labLoading}
                    onClick={() => {
                      setLabTab('reflect');
                      handleReflect();
                    }}
                  >
                    {labLoading && labTab === 'reflect' ? 'Reflecting...' : '🔮 Synthesize Reflection'}
                  </button>
                </div>
              </div>
            </div>

            {labError && <div className="page-error-alert">{labError}</div>}

            {/* Results Area */}
            <div className="explorer-results">
              {labTab === 'recall' && (
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

              {labTab === 'reflect' && (
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
      )}

      {/* ============================================================== */}
      {/* SLIDE-OVER INSPECTION DRAWER / MODAL                           */}
      {/* ============================================================== */}
      {selectedMemory && (
        <div className="drawer-overlay" onClick={handleCloseDetail}>
          <div
            className="drawer-panel"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            {/* Drawer Header */}
            <div className="drawer-header">
              <div className="drawer-header-title">
                <span className="drawer-inc-id">{selectedMemory.incident_id}</span>
                <h3>{selectedMemory.title}</h3>
              </div>
              <button
                type="button"
                className="drawer-close-btn"
                onClick={handleCloseDetail}
                title="Close drawer"
              >
                ✕
              </button>
            </div>

            {/* Badges Bar */}
            <div className="drawer-badges-bar">
              {selectedMemory.verified ? (
                <span className="badge-verified-pill">✓ Confirmed Human Fix</span>
              ) : (
                <span className="badge-unverified-pill">⚠️ Unverified Record</span>
              )}
              <span className="meta-tag service-tag">{selectedMemory.service}</span>
              <span className="meta-tag env-tag">{selectedMemory.environment}</span>
              <span className="meta-tag provider-tag">● {selectedMemory.storage_provider}</span>
              <span className="meta-tag bank-tag">Bank: {selectedMemory.bank_id}</span>
              {!selectedMemory.has_parent_incident && (
                <span className="meta-tag orphan-tag">Standalone Memory Record</span>
              )}
            </div>

            {/* Drawer Body Content */}
            <div className="drawer-body">
              {/* Human Verification Box */}
              <div className="detail-section verification-box">
                <div className="section-title-sm">
                  <span>🛡️ Human Verification Sign-off</span>
                </div>
                <div className="verification-details-grid">
                  <div>
                    <span className="v-label">Verified Engineer:</span>
                    <strong className="v-val">{selectedMemory.engineer || 'On-Call Engineer'}</strong>
                  </div>
                  <div>
                    <span className="v-label">Resolved At:</span>
                    <span className="v-val">{formatDate(selectedMemory.created_at)}</span>
                  </div>
                  <div>
                    <span className="v-label">Resolution Status:</span>
                    <span className="v-val status-text-resolved">{selectedMemory.outcome}</span>
                  </div>
                  <div>
                    <span className="v-label">Recall Reuse Count:</span>
                    <span className="v-val font-mono">
                      {selectedMemory.recall_count} subsequent incident citation{selectedMemory.recall_count !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>
              </div>

              {/* Confirmed Root Cause */}
              <div className="detail-section">
                <div className="section-title-sm">
                  <span>🎯 Confirmed Root Cause</span>
                </div>
                <div className="content-box root-cause-box">
                  <p>{selectedMemory.root_cause}</p>
                </div>
              </div>

              {/* Verified Resolution Steps */}
              <div className="detail-section">
                <div className="section-title-sm">
                  <span>🔧 Verified Resolution Steps</span>
                </div>
                <div className="content-box resolution-box">
                  <pre className="resolution-pre">{selectedMemory.resolution}</pre>
                </div>
              </div>

              {/* Observed Symptoms */}
              {selectedMemory.symptoms && (
                <div className="detail-section">
                  <div className="section-title-sm">
                    <span>⚠️ Observed Failure Symptoms</span>
                  </div>
                  <div className="content-box symptoms-box">
                    <p>{selectedMemory.symptoms}</p>
                  </div>
                </div>
              )}

              {/* Sanitized Evidence Logs */}
              {selectedMemory.evidence_logs && (
                <div className="detail-section">
                  <div className="section-title-sm">
                    <span>🔒 Sanitized Evidence Logs</span>
                    <span className="sanitizer-badge">Tokens &amp; passwords redacted</span>
                  </div>
                  <pre className="evidence-logs-pre">{selectedMemory.evidence_logs}</pre>
                </div>
              )}

              {/* Recall References */}
              {selectedMemory.recalled_in_incidents && selectedMemory.recalled_in_incidents.length > 0 && (
                <div className="detail-section">
                  <div className="section-title-sm">
                    <span>🔁 Incidents Recalling This Memory ({selectedMemory.recalled_in_incidents.length})</span>
                  </div>
                  <div className="citation-incidents-list">
                    {selectedMemory.recalled_in_incidents.map((cInc) => (
                      <div key={cInc.id} className="citation-incident-item">
                        <span className="citation-inc-id">{cInc.id}</span>
                        <span className="citation-inc-title">{cInc.title}</span>
                        <span className="citation-inc-service">{cInc.service}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Raw Memory Content (Collapsible) */}
              <div className="detail-section raw-content-section">
                <details className="raw-details-toggle">
                  <summary className="raw-summary">View Raw Persistent Memory Payload</summary>
                  <pre className="raw-memory-pre">{selectedMemory.content}</pre>
                </details>
              </div>
            </div>

            {/* Drawer Footer */}
            <div className="drawer-footer">
              <button
                type="button"
                className="secondary-btn"
                onClick={handleCloseDetail}
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
