const RAW_BASE = import.meta.env.VITE_API_BASE_URL || 'https://opsrecall-ai.onrender.com/';
const API_BASE = RAW_BASE.replace(/\/+$/, '');

async function request(endpoint, options = {}) {
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE}${normalizedEndpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}

export const api = {
  getHealth: () => request('/api/health'),

  getDashboardSummary: () => request('/api/dashboard/summary'),

  getDashboardAnalytics: () => request('/api/dashboard/analytics'),

  listIncidents: (params = {}) => {
    const searchParams = new URLSearchParams();
    if (params.search) searchParams.append('search', params.search);
    if (params.service) searchParams.append('service', params.service);
    if (params.status) searchParams.append('status', params.status);
    const queryString = searchParams.toString();
    return request(`/api/incidents${queryString ? `?${queryString}` : ''}`);
  },

  getIncident: (id) => request(`/api/incidents/${id}`),

  createIncident: (incidentData) =>
    request('/api/incidents', {
      method: 'POST',
      body: JSON.stringify(incidentData),
    }),

  saveFeedback: (id, feedback) =>
    request(`/api/incidents/${id}/feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    }),

  saveResolution: (id, resolution) =>
    request(`/api/incidents/${id}/resolution`, {
      method: 'POST',
      body: JSON.stringify(resolution),
    }),

  listIncidentActions: (incidentId, params = {}) => {
    const searchParams = new URLSearchParams();
    if (params.status) searchParams.append('status', params.status);
    if (params.category) searchParams.append('category', params.category);
    const queryString = searchParams.toString();
    return request(`/api/incidents/${incidentId}/actions${queryString ? `?${queryString}` : ''}`);
  },

  createIncidentAction: (incidentId, actionData) =>
    request(`/api/incidents/${incidentId}/actions`, {
      method: 'POST',
      body: JSON.stringify(actionData),
    }),

  importRecommendedActions: (incidentId, actor = 'On-call Engineer') =>
    request(`/api/incidents/${incidentId}/actions/import-recommendations`, {
      method: 'POST',
      body: JSON.stringify({ actor }),
    }),

  updateIncidentAction: (incidentId, actionId, updateData) =>
    request(`/api/incidents/${incidentId}/actions/${actionId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    }),

  getIncidentAction: (incidentId, actionId) =>
    request(`/api/incidents/${incidentId}/actions/${actionId}`),

  getActionPlanSummary: (incidentId) =>
    request(`/api/incidents/${incidentId}/actions/summary`),

  getIncidentTimeline: (incidentId, limit = 150) =>
    request(`/api/incidents/${incidentId}/timeline?limit=${limit}`),

  listMemories: (params = {}) => {
    const searchParams = new URLSearchParams();
    if (params.search) searchParams.append('search', params.search);
    if (params.service) searchParams.append('service', params.service);
    if (params.severity) searchParams.append('severity', params.severity);
    if (params.environment) searchParams.append('environment', params.environment);
    if (params.verified !== undefined && params.verified !== null) {
      searchParams.append('verified', params.verified);
    }
    if (params.page) searchParams.append('page', params.page);
    if (params.pageSize || params.page_size) {
      searchParams.append('page_size', params.pageSize || params.page_size);
    }
    const queryString = searchParams.toString();
    return request(`/api/memory${queryString ? `?${queryString}` : ''}`);
  },

  getMemoryDetail: (id) => request(`/api/memory/${id}`),

  recallMemory: (query, budget = 'mid') =>
    request('/api/memory/recall', {
      method: 'POST',
      body: JSON.stringify({ query, budget }),
    }),

  reflectMemory: (query, budget = 'mid') =>
    request('/api/memory/reflect', {
      method: 'POST',
      body: JSON.stringify({ query, budget }),
    }),
};
