import { useEffect, useState } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'

const initialForm = {
  title: 'Orders API returning 500 errors',
  service: 'orders-api',
  environment: 'staging',
  description: 'Requests began failing after the latest deployment.',
  logs: 'Database connection acquisition timed out after 30 seconds. Worker queue backlog started increasing.',
  deployment_context: 'Release 1.4.2',
}

function App() {
  const [form, setForm] = useState(initialForm)
  const [incidents, setIncidents] = useState([])
  const [dashboard, setDashboard] = useState({ total_incidents: 0, resolved_incidents: 0, by_status: {} })
  const [selection, setSelection] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [resolution, setResolution] = useState({ root_cause: '', resolution: '', engineer: 'Ops team' })

  useEffect(() => {
    loadIncidents()
    loadSummary()
  }, [])

  async function loadIncidents() {
    try {
      const response = await fetch(`${API_BASE}/api/incidents`)
      if (!response.ok) throw new Error('Unable to fetch incidents')
      const data = await response.json()
      setIncidents(data)
      if (data.length > 0) {
        setSelection(data[0])
      }
    } catch (err) {
      setError(err.message)
    }
  }

  async function loadSummary() {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/summary`)
      if (!response.ok) throw new Error('Unable to fetch dashboard summary')
      const data = await response.json()
      setDashboard(data)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')

    try {
      const response = await fetch(`${API_BASE}/api/incidents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Unable to submit incident')
      }

      const data = await response.json()
      setAnalysis(data.analysis)
      setSelection({ id: data.incident_id, title: form.title, service: form.service, environment: form.environment, status: data.status, analysis: data.analysis })
      setResolution((current) => ({ ...current, root_cause: '', resolution: '' }))
      await loadIncidents()
      await loadSummary()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleResolutionSave() {
    if (!selection?.id) return

    try {
      const response = await fetch(`${API_BASE}/api/incidents/${selection.id}/resolution`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          root_cause: resolution.root_cause,
          resolution: resolution.resolution,
          engineer: resolution.engineer,
          verified: true,
        }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Unable to save resolution')
      }

      setError('')
      await loadIncidents()
      await loadSummary()
      setResolution({ root_cause: '', resolution: '', engineer: 'Ops team' })
    } catch (err) {
      setError(err.message)
    }
  }

  const activeIncident = selection || incidents[0] || null

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">OpsRecall AI</p>
          <h1>Incident memory</h1>
        </div>
        <nav className="nav">
          <button type="button" className="nav-button active">New incident</button>
          <button type="button" className="nav-button">History</button>
          <button type="button" className="nav-button">Memory</button>
        </nav>
        <div className="incident-list">
          <h3>Recent incidents</h3>
          {incidents.length === 0 ? (
            <p className="empty-state">No incidents yet</p>
          ) : (
            incidents.map((incident) => (
              <button
                key={incident.id}
                type="button"
                className={`incident-item ${activeIncident?.id === incident.id ? 'selected' : ''}`}
                onClick={() => setSelection(incident)}
              >
                <strong>{incident.title}</strong>
                <span>{incident.service}</span>
                <small>{incident.status}</small>
              </button>
            ))
          )}
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow muted">Operations response</p>
            <h2>Persistent incident recall</h2>
          </div>
          <div className="status-pill">{dashboard.resolved_incidents || 0} resolved</div>
        </header>

        <section className="stats-row">
          <div className="stat-card">
            <span>Total incidents</span>
            <strong>{dashboard.total_incidents || 0}</strong>
          </div>
          <div className="stat-card">
            <span>Resolved</span>
            <strong>{dashboard.resolved_incidents || 0}</strong>
          </div>
          <div className="stat-card">
            <span>Open</span>
            <strong>{Math.max((dashboard.total_incidents || 0) - (dashboard.resolved_incidents || 0), 0)}</strong>
          </div>
        </section>

        <div className="content-grid">
          <section className="panel form-panel">
            <h3>Submit new incident</h3>
            <form onSubmit={handleSubmit} className="incident-form">
              <label>
                Title
                <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              </label>
              <div className="two-column">
                <label>
                  Service
                  <input value={form.service} onChange={(e) => setForm({ ...form, service: e.target.value })} />
                </label>
                <label>
                  Environment
                  <input value={form.environment} onChange={(e) => setForm({ ...form, environment: e.target.value })} />
                </label>
              </div>
              <label>
                Description
                <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={4} />
              </label>
              <label>
                Deployment context
                <input value={form.deployment_context || ''} onChange={(e) => setForm({ ...form, deployment_context: e.target.value })} />
              </label>
              <label>
                Error logs
                <textarea value={form.logs} onChange={(e) => setForm({ ...form, logs: e.target.value })} rows={6} />
              </label>
              {error ? <p className="error-box">{error}</p> : null}
              <button type="submit" className="primary-button" disabled={submitting}>
                {submitting ? 'Analyzing…' : 'Analyze incident'}
              </button>
            </form>
          </section>

          <section className="panel analysis-panel">
            <h3>Current analysis</h3>
            {analysis ? (
              <>
                <div className="analysis-summary">
                  <span className="badge">{analysis.confidence || 'medium'}</span>
                  <p>{analysis.summary}</p>
                </div>
                {analysis.analysis_notice ? (
                  <p className="analysis-notice">{analysis.analysis_notice}</p>
                ) : null}
                <div className="chips">
                  {analysis.symptoms?.map((symptom) => <span key={symptom} className="chip">{symptom}</span>)}
                </div>
                <div className="section-block">
                  <h4>Possible causes</h4>
                  {analysis.possible_causes?.map((item) => (
                    <div key={item.cause} className="list-box">
                      <strong>{item.cause}</strong>
                      <ul>
                        {item.evidence?.map((evidence) => <li key={evidence}>{evidence}</li>)}
                      </ul>
                    </div>
                  ))}
                </div>
                <div className="section-block">
                  <h4>Recommended checks</h4>
                  <ul>
                    {analysis.recommended_checks?.map((step) => <li key={step}>{step}</li>)}
                  </ul>
                </div>
                <div className="section-block">
                  <h4>Related memory</h4>
                  {analysis.related_memory_insights?.length ? (
                    <ul>
                      {analysis.related_memory_insights.map((memory) => (
                        <li key={`${memory.incident_id}-${memory.lesson}`}>
                          <strong>{memory.incident_id}</strong>: {memory.lesson}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No prior memory matched this incident yet.</p>
                  )}
                </div>
              </>
            ) : (
              <p className="empty-state">Submit an incident to generate a diagnosis.</p>
            )}
          </section>
        </div>

        {activeIncident ? (
          <section className="panel resolution-panel">
            <h3>Resolution tracking</h3>
            <div className="resolution-meta">
              <span>{activeIncident.id}</span>
              <span>{activeIncident.service}</span>
              <span>{activeIncident.environment}</span>
            </div>
            <div className="resolution-form">
              <label>
                Root cause
                <input value={resolution.root_cause} onChange={(e) => setResolution({ ...resolution, root_cause: e.target.value })} />
              </label>
              <label>
                Resolution
                <textarea value={resolution.resolution} onChange={(e) => setResolution({ ...resolution, resolution: e.target.value })} rows={4} />
              </label>
              <label>
                Engineer
                <input value={resolution.engineer} onChange={(e) => setResolution({ ...resolution, engineer: e.target.value })} />
              </label>
              <button type="button" className="primary-button" onClick={handleResolutionSave}>Save verified resolution</button>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  )
}

export default App
