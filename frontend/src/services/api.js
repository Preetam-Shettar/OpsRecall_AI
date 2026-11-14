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
