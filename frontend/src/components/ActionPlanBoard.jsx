import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { formatDate } from '../utils/formatters';

export default function ActionPlanBoard({ incident, onProceedToResolution }) {
  const [actions, setActions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [importing, setImporting] = useState(false);
  const [activeModalAction, setActiveModalAction] = useState(null); // { action, type: 'complete' | 'block' | 'assign' }
  const [modalInput, setModalInput] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  // New action form state
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newCategory, setNewCategory] = useState('read_only');
  const [newPriority, setNewPriority] = useState('medium');
  const [newEngineer, setNewEngineer] = useState('');
  const [newCommand, setNewCommand] = useState('');

  useEffect(() => {
    if (incident?.id) {
      loadActions();
    }
  }, [incident?.id]);

  async function loadActions() {
    setLoading(true);
    setError(null);
    try {
      const [listRes, summaryRes] = await Promise.all([
        api.listIncidentActions(incident.id),
        api.getActionPlanSummary(incident.id),
      ]);
      setActions(listRes || []);
      setSummary(summaryRes || null);
    } catch (err) {
      setError(err.message || 'Failed to load action plan');
    } finally {
      setLoading(false);
    }
  }

  async function handleImportRecommendations() {
    setImporting(true);
    setError(null);
    try {
      await api.importRecommendedActions(incident.id, 'On-call Engineer');
      await loadActions();
    } catch (err) {
      setError(err.message || 'Failed to import diagnostic recommendations');
    } finally {
      setImporting(false);
    }
  }

  async function handleCreateAction(e) {
    e.preventDefault();
    if (!newTitle.trim()) return;

    setError(null);
    try {
      await api.createIncidentAction(incident.id, {
        title: newTitle.trim(),
        description: newDesc.trim(),
        category: newCategory,
        priority: newPriority,
        assigned_engineer: newEngineer.trim() || undefined,
        command_hint: newCommand.trim() || undefined,
        actor: newEngineer.trim() || 'On-call Engineer',
      });
      setNewTitle('');
      setNewDesc('');
      setNewCommand('');
      setNewEngineer('');
      setShowAddForm(false);
      await loadActions();
    } catch (err) {
      setError(err.message || 'Failed to create action');
    }
  }

  async function handleStatusChange(action, nextStatus) {
    if (nextStatus === 'completed') {
      setActiveModalAction({ action, type: 'complete' });
      setModalInput('');
      return;
    }
    if (nextStatus === 'blocked') {
      setActiveModalAction({ action, type: 'block' });
      setModalInput('');
      return;
    }

    // Direct transition for in_progress or pending
    try {
      await api.updateIncidentAction(incident.id, action.id, {
        status: nextStatus,
        actor: action.assigned_engineer || 'On-call Engineer',
      });
      await loadActions();
    } catch (err) {
      setError(err.message || 'Failed to update action status');
    }
  }

  async function submitModalAction(e) {
    e.preventDefault();
    if (!activeModalAction) return;
    const { action, type } = activeModalAction;

    try {
      if (type === 'complete') {
        await api.updateIncidentAction(incident.id, action.id, {
          status: 'completed',
          completion_notes: modalInput.trim() || 'Action completed and verified by engineer.',
          actor: action.assigned_engineer || 'On-call Engineer',
        });
      } else if (type === 'block') {
        await api.updateIncidentAction(incident.id, action.id, {
          status: 'blocked',
          blocked_reason: modalInput.trim() || 'Blocked pending external dependency or access.',
          actor: action.assigned_engineer || 'On-call Engineer',
        });
      } else if (type === 'assign') {
        await api.updateIncidentAction(incident.id, action.id, {
          assigned_engineer: modalInput.trim() || undefined,
          actor: 'On-call Engineer',
        });
      }
      setActiveModalAction(null);
      setModalInput('');
      await loadActions();
    } catch (err) {
      setError(err.message || 'Failed to update action');
    }
  }

  function handleCopyCommand(actionId, cmd) {
    if (!cmd) return;
    navigator.clipboard.writeText(cmd);
    setCopiedId(actionId);
    setTimeout(() => setCopiedId(null), 2000);
  }

  function handleCompileAndProceed() {
    const findingsList = actions
      .filter((a) => a.status === 'completed' && a.completion_notes)
      .map((a) => `• ${a.title}: ${a.completion_notes}`);

    const summaryText = findingsList.length > 0
      ? `Action plan findings:\n${findingsList.join('\n')}`
      : 'Action plan checks completed.';

    if (onProceedToResolution) {
      onProceedToResolution(summaryText);
    }
  }

  // Filter actions
  const filteredActions = actions.filter((a) => {
    if (statusFilter !== 'all' && a.status !== statusFilter) return false;
    if (categoryFilter !== 'all' && a.category !== categoryFilter) return false;
    return true;
  });

  const total = summary?.total_actions || actions.length;
  const completed = summary?.completed_actions || actions.filter((a) => a.status === 'completed').length;
  const blocked = summary?.blocked_actions || actions.filter((a) => a.status === 'blocked').length;
  const inProgress = summary?.in_progress_actions || actions.filter((a) => a.status === 'in_progress').length;
  const pending = summary?.pending_actions || actions.filter((a) => a.status === 'pending').length;
  const progressPct = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div className="action-plan-workspace">
      {/* Overview & Progress Meter */}
      <div className="action-plan-header-card">
        <div className="action-header-left">
          <div className="action-plan-title-row">
            <span className="plan-badge">RESPONSE WORKSPACE</span>
            <h3>Incident Action Plan</h3>
          </div>
          <p className="action-plan-subtitle">
            Engineer-guided diagnostic execution, mitigation tracking, and real-time finding collection.
          </p>

          <div className="action-progress-wrapper">
            <div className="action-progress-meta">
              <span className="progress-label">Response Progress: <strong>{progressPct}%</strong></span>
              <span className="progress-counts">{completed} of {total} actions completed</span>
            </div>
            <div className="action-progress-track">
              <div
                className="action-progress-fill"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        </div>

        <div className="action-header-stats-grid">
          <div className="action-mini-stat stat-pending">
            <span className="mini-stat-val">{pending}</span>
            <span className="mini-stat-label">Pending</span>
          </div>
          <div className="action-mini-stat stat-in-progress">
            <span className="mini-stat-val">{inProgress}</span>
            <span className="mini-stat-label">In Progress</span>
          </div>
          <div className="action-mini-stat stat-completed">
            <span className="mini-stat-val">{completed}</span>
            <span className="mini-stat-label">Completed</span>
          </div>
          <div className="action-mini-stat stat-blocked">
            <span className="mini-stat-val">{blocked}</span>
            <span className="mini-stat-label">Blocked</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="page-error-alert" role="alert">
          <span>⚠️ {error}</span>
          <button type="button" className="close-alert-btn" onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Toolbar & Filter Bar */}
      <div className="action-toolbar">
        <div className="toolbar-filters-group">
          {/* Status Filters */}
          <div className="action-filter-pills">
            <button
              type="button"
              className={`action-pill ${statusFilter === 'all' ? 'active' : ''}`}
              onClick={() => setStatusFilter('all')}
            >
              All ({total})
            </button>
            <button
              type="button"
              className={`action-pill pill-pending ${statusFilter === 'pending' ? 'active' : ''}`}
              onClick={() => setStatusFilter('pending')}
            >
              Pending ({pending})
            </button>
            <button
              type="button"
              className={`action-pill pill-inprogress ${statusFilter === 'in_progress' ? 'active' : ''}`}
              onClick={() => setStatusFilter('in_progress')}
            >
              In Progress ({inProgress})
            </button>
            <button
              type="button"
              className={`action-pill pill-completed ${statusFilter === 'completed' ? 'active' : ''}`}
              onClick={() => setStatusFilter('completed')}
            >
              Completed ({completed})
            </button>
            <button
              type="button"
              className={`action-pill pill-blocked ${statusFilter === 'blocked' ? 'active' : ''}`}
              onClick={() => setStatusFilter('blocked')}
            >
              Blocked ({blocked})
            </button>
          </div>

          {/* Category Dropdown */}
          <div className="category-select-wrapper">
            <label htmlFor="action-category-filter" className="sr-only">Category</label>
            <select
              id="action-category-filter"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="action-select-input"
            >
              <option value="all">All Categories</option>
              <option value="read_only">Read-Only Checks</option>
              <option value="active_validation">Active Validations</option>
              <option value="mitigation">Mitigations</option>
            </select>
          </div>
        </div>

        <div className="toolbar-actions-group">
          <button
            type="button"
            className="action-btn-import"
            onClick={handleImportRecommendations}
            disabled={importing}
            title="Import recommended checks from Part 3 explainable diagnosis"
          >
            {importing ? 'Importing…' : '⚡ Import AI Checks'}
          </button>
          <button
            type="button"
            className="action-btn-add"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? '✕ Cancel' : '➕ Add Action'}
          </button>
        </div>
      </div>

      {/* Manual Action Form Drawer / Inset */}
      {showAddForm && (
        <form className="add-action-form-panel" onSubmit={handleCreateAction}>
          <h4>Add Response Action</h4>
          <div className="form-row-2">
            <div className="form-group">
              <label htmlFor="new-action-title">Action Title *</label>
              <input
                id="new-action-title"
                type="text"
                className="input-field"
                placeholder="e.g. Inspect connection pool saturation on replica"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="new-action-category">Safety Classification</label>
              <select
                id="new-action-category"
                className="input-field"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
              >
                <option value="read_only">Read-Only Check (Safe)</option>
                <option value="active_validation">Active Validation (Non-mutating probe)</option>
                <option value="mitigation">Mitigation / Remediation Action</option>
              </select>
            </div>
          </div>

          <div className="form-row-3">
            <div className="form-group">
              <label htmlFor="new-action-priority">Priority</label>
              <select
                id="new-action-priority"
                className="input-field"
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value)}
              >
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="new-action-engineer">Assign Engineer</label>
              <input
                id="new-action-engineer"
                type="text"
                className="input-field"
                placeholder="e.g. Alice / On-call SRE"
                value={newEngineer}
                onChange={(e) => setNewEngineer(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="new-action-command">Command Hint (Optional)</label>
              <input
                id="new-action-command"
                type="text"
                className="input-field font-mono"
                placeholder="e.g. kubectl logs -l app=orders-api --tail=100"
                value={newCommand}
                onChange={(e) => setNewCommand(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="new-action-desc">Description / Instructions</label>
            <textarea
              id="new-action-desc"
              className="textarea-field"
              rows={2}
              placeholder="Provide specific validation criteria or expected diagnostic output..."
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
            />
          </div>

          <div className="form-actions-right">
            <button type="button" className="secondary-btn" onClick={() => setShowAddForm(false)}>
              Cancel
            </button>
            <button type="submit" className="primary-action-btn">
              Create Action Item
            </button>
          </div>
        </form>
      )}

      {/* Action Cards List */}
      {loading ? (
        <div className="action-plan-loading">
          <div className="loading-spinner-small" />
          <p>Loading incident action plan…</p>
        </div>
      ) : filteredActions.length === 0 ? (
        <div className="action-plan-empty-card">
          <span className="empty-icon">📋</span>
          <h4>No actions found</h4>
          <p>
            {actions.length === 0
              ? 'No response actions created yet. Import AI diagnostic checks or add custom tasks to guide response.'
              : 'No actions match the selected filter criteria.'}
          </p>
          {actions.length === 0 && (
            <button
              type="button"
              className="primary-action-btn mt-3"
              onClick={handleImportRecommendations}
              disabled={importing}
            >
              ⚡ Import AI Diagnostic Checks ({incident.analysis?.recommended_checks?.length || 0})
            </button>
          )}
        </div>
      ) : (
        <div className="action-cards-grid">
          {filteredActions.map((action) => {
            const isCompleted = action.status === 'completed';
            const isBlocked = action.status === 'blocked';
            const isInProgress = action.status === 'in_progress';

            return (
              <div
                key={action.id}
                className={`action-card action-status-${action.status} action-cat-${action.category}`}
              >
                <div className="action-card-top">
                  <div className="action-badges-left">
                    <span className={`action-cat-pill cat-${action.category}`}>
                      {action.category.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className={`action-priority-pill priority-${action.priority}`}>
                      {action.priority.toUpperCase()}
                    </span>
                  </div>

                  <span className={`action-status-pill status-${action.status}`}>
                    {action.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>

                <div className="action-card-main">
                  <h4 className="action-card-title">{action.title}</h4>
                  {action.description && (
                    <p className="action-card-desc">{action.description}</p>
                  )}

                  {/* Command Hint Box */}
                  {action.command_hint && (
                    <div className="action-command-box">
                      <div className="command-box-header">
                        <span className="command-label">COMMAND HINT</span>
                        <button
                          type="button"
                          className="copy-command-btn"
                          onClick={() => handleCopyCommand(action.id, action.command_hint)}
                          title="Copy command to clipboard"
                        >
                          {copiedId === action.id ? '✓ Copied' : '📋 Copy'}
                        </button>
                      </div>
                      <code className="command-code">{action.command_hint}</code>
                      <span className="command-disclaimer">
                        🔒 Safe diagnostic hint. OpsRecall AI never executes shell commands automatically.
                      </span>
                    </div>
                  )}

                  {/* Blocked Reason Banner */}
                  {isBlocked && action.blocked_reason && (
                    <div className="action-blocked-banner">
                      <strong>⛔ Blocker Reason:</strong> {action.blocked_reason}
                    </div>
                  )}

                  {/* Findings Banner */}
                  {isCompleted && action.completion_notes && (
                    <div className="action-findings-banner">
                      <strong>✅ Recorded Findings:</strong> {action.completion_notes}
                    </div>
                  )}
                </div>

                <div className="action-card-footer">
                  <div className="action-assignee-row">
                    <span className="assignee-label">Assignee:</span>
                    <button
                      type="button"
                      className="assignee-btn"
                      onClick={() => {
                        setActiveModalAction({ action, type: 'assign' });
                        setModalInput(action.assigned_engineer || '');
                      }}
                      title="Click to change assignee"
                    >
                      👤 {action.assigned_engineer || 'Unassigned (Assign)'}
                    </button>
                  </div>

                  <div className="action-controls-row">
                    {action.status === 'pending' && (
                      <button
                        type="button"
                        className="btn-action-start"
                        onClick={() => handleStatusChange(action, 'in_progress')}
                      >
                        ▶ Start Action
                      </button>
                    )}

                    {isInProgress && (
                      <>
                        <button
                          type="button"
                          className="btn-action-block"
                          onClick={() => handleStatusChange(action, 'blocked')}
                        >
                          ⛔ Block
                        </button>
                        <button
                          type="button"
                          className="btn-action-complete"
                          onClick={() => handleStatusChange(action, 'completed')}
                        >
                          ✔ Complete &amp; Log Findings
                        </button>
                      </>
                    )}

                    {isBlocked && (
                      <button
                        type="button"
                        className="btn-action-resume"
                        onClick={() => handleStatusChange(action, 'in_progress')}
                      >
                        ↺ Resume Action
                      </button>
                    )}

                    {isCompleted && (
                      <button
                        type="button"
                        className="btn-action-reopen"
                        onClick={() => handleStatusChange(action, 'in_progress')}
                        title="Reopen action if further diagnosis is required"
                      >
                        ↺ Reopen
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Completion Banner & Resolution Handoff */}
      {completed > 0 && (
        <div className="action-handoff-banner">
          <div className="handoff-text">
            <h4>Ready to Confirm Resolution?</h4>
            <p>
              {completed} of {total} actions completed with verified findings. Carry these findings directly into the engineer resolution record.
            </p>
          </div>
          <button
            type="button"
            className="primary-action-btn handoff-cta-btn"
            onClick={handleCompileAndProceed}
          >
            Proceed to Verified Resolution →
          </button>
        </div>
      )}

      {/* Action Dialog / Modal */}
      {activeModalAction && (
        <div className="action-modal-backdrop" onClick={() => setActiveModalAction(null)}>
          <div className="action-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h4>
                {activeModalAction.type === 'complete' && 'Complete Action & Log Findings'}
                {activeModalAction.type === 'block' && 'Mark Action as Blocked'}
                {activeModalAction.type === 'assign' && 'Assign Engineer'}
              </h4>
              <button
                type="button"
                className="close-modal-btn"
                onClick={() => setActiveModalAction(null)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={submitModalAction}>
              <div className="modal-body">
                <p className="modal-action-title">
                  <strong>Action:</strong> {activeModalAction.action.title}
                </p>

                {activeModalAction.type === 'complete' && (
                  <div className="form-group">
                    <label htmlFor="modal-notes">
                      Diagnostic Findings / Remediation Notes *
                    </label>
                    <textarea
                      id="modal-notes"
                      className="textarea-field"
                      rows={3}
                      placeholder="e.g. Verified lock contention was resolved after pool ceiling increase. Error rate dropped to 0%."
                      value={modalInput}
                      onChange={(e) => setModalInput(e.target.value)}
                      required
                      autoFocus
                    />
                    <span className="field-hint">
                      These findings will be carried into the verified resolution record.
                    </span>
                  </div>
                )}

                {activeModalAction.type === 'block' && (
                  <div className="form-group">
                    <label htmlFor="modal-block-reason">
                      Reason for Blocking *
                    </label>
                    <textarea
                      id="modal-block-reason"
                      className="textarea-field"
                      rows={2}
                      placeholder="e.g. Waiting on production database credentials or infrastructure freeze lift."
                      value={modalInput}
                      onChange={(e) => setModalInput(e.target.value)}
                      required
                      autoFocus
                    />
                  </div>
                )}

                {activeModalAction.type === 'assign' && (
                  <div className="form-group">
                    <label htmlFor="modal-engineer-name">
                      Engineer Name / Team Handle
                    </label>
                    <input
                      id="modal-engineer-name"
                      type="text"
                      className="input-field"
                      placeholder="e.g. Alice / Incident Lead"
                      value={modalInput}
                      onChange={(e) => setModalInput(e.target.value)}
                      required
                      autoFocus
                    />
                  </div>
                )}
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() => setActiveModalAction(null)}
                >
                  Cancel
                </button>
                <button type="submit" className="primary-action-btn">
                  {activeModalAction.type === 'complete' && 'Save Findings & Complete'}
                  {activeModalAction.type === 'block' && 'Save & Block Action'}
                  {activeModalAction.type === 'assign' && 'Update Assignee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
