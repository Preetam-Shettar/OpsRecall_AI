import React, { useEffect, useState } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import NewIncident from './pages/NewIncident';
import IncidentHistory from './pages/IncidentHistory';
import IncidentDetails from './pages/IncidentDetails';
import MemoryExplorer from './pages/MemoryExplorer';
import { api } from './services/api';
import './App.css';

export default function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [viewHistory, setViewHistory] = useState(['dashboard']);
  const [theme, setTheme] = useState(() => localStorage.getItem('opsrecall_theme') || 'obsidian');
  const [incidents, setIncidents] = useState([]);
  const [dashboard, setDashboard] = useState({
    total_incidents: 0,
    resolved_incidents: 0,
    open_incidents: 0,
    stored_memories: 0,
    by_status: {},
  });
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [submittedIncident, setSubmittedIncident] = useState(null);
  const [backendHealthy, setBackendHealthy] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('opsrecall_theme', theme);
  }, [theme]);

  useEffect(() => {
    bootstrap();
    const interval = setInterval(checkBackendHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  async function checkBackendHealth() {
    try {
      const res = await api.getHealth();
      setBackendHealthy(res.status === 'ok');
    } catch {
      setBackendHealthy(false);
    }
  }

  async function bootstrap() {
    await checkBackendHealth();
    await Promise.all([loadIncidents(), loadSummary()]);
  }

  async function handleRefresh() {
    setIsRefreshing(true);
    try {
      await checkBackendHealth();
      await Promise.all([loadIncidents(), loadSummary()]);
    } finally {
      setTimeout(() => setIsRefreshing(false), 300);
    }
  }

  function navigateTo(nextView) {
    if (nextView === activeView) return;
    setViewHistory((prev) => [...prev, nextView]);
    setActiveView(nextView);
    setIsSidebarOpen(false);
  }

  function handleBack() {
    if (viewHistory.length > 1) {
      const updated = [...viewHistory];
      updated.pop(); // remove current view
      const prev = updated[updated.length - 1];
      setViewHistory(updated);
      setActiveView(prev);
    } else {
      setActiveView('dashboard');
      setViewHistory(['dashboard']);
    }
  }

  async function loadIncidents() {
    try {
      const data = await api.listIncidents();
      setIncidents(data);
    } catch (err) {
      console.error('Failed to load incidents', err);
    }
  }

  async function loadSummary() {
    try {
      const data = await api.getDashboardSummary();
      setDashboard(data);
    } catch (err) {
      console.error('Failed to load dashboard summary', err);
    }
  }

  async function handleSubmitIncident(formData) {
    setIsSubmitting(true);
    try {
      const response = await api.createIncident(formData);
      setSubmittedIncident(response);
      await Promise.all([loadIncidents(), loadSummary()]);
      return response;
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSaveResolution(resolutionData) {
    const targetId = submittedIncident?.incident_id || submittedIncident?.id || selectedIncident?.id;
    if (!targetId) return;

    await api.saveResolution(targetId, resolutionData);

    // Refresh state
    await Promise.all([loadIncidents(), loadSummary()]);

    // Update locally selected/submitted incident
    if (selectedIncident && selectedIncident.id === targetId) {
      const updated = await api.getIncident(targetId);
      setSelectedIncident(updated);
    }
    if (submittedIncident && (submittedIncident.incident_id === targetId || submittedIncident.id === targetId)) {
      const updated = await api.getIncident(targetId);
      setSubmittedIncident(updated);
    }
  }

  function handleSelectIncident(incident) {
    setSelectedIncident(incident);
    navigateTo('details');
  }

  function handleNavigateNew() {
    navigateTo('newIncident');
  }

  return (
    <div className="app-layout">
      <Sidebar
        activeView={activeView}
        setActiveView={navigateTo}
        counts={{
          total_incidents: dashboard.total_incidents,
          stored_memories: dashboard.stored_memories,
        }}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <div className="app-main-viewport">
        <Navbar
          activeView={activeView}
          backendHealthy={backendHealthy}
          theme={theme}
          onThemeChange={setTheme}
          canGoBack={activeView !== 'dashboard'}
          onBack={handleBack}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        />

        <main className="content-container">
          {activeView === 'dashboard' && (
            <Dashboard
              dashboard={dashboard}
              recentIncidents={incidents.slice(0, 6)}
              onNavigateNew={handleNavigateNew}
              onNavigateHistory={() => navigateTo('history')}
              onNavigateMemory={() => navigateTo('memory')}
              onSelectIncident={handleSelectIncident}
              onRefresh={handleRefresh}
              isRefreshing={isRefreshing}
            />
          )}

          {activeView === 'newIncident' && (
            <NewIncident
              onSubmitIncident={handleSubmitIncident}
              onSaveResolution={handleSaveResolution}
              isSubmitting={isSubmitting}
              submittedIncident={submittedIncident}
            />
          )}

          {activeView === 'history' && (
            <IncidentHistory
              incidents={incidents}
              onSelectIncident={handleSelectIncident}
              onNavigateNew={handleNavigateNew}
            />
          )}

          {activeView === 'details' && (
            <IncidentDetails
              incident={selectedIncident}
              onSaveResolution={handleSaveResolution}
              onBack={handleBack}
            />
          )}

          {activeView === 'memory' && <MemoryExplorer />}
        </main>
      </div>
    </div>
  );
}
