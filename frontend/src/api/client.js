const BASE_URL = '/api'

function getToken() {
  return localStorage.getItem('apexus_token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    localStorage.removeItem('apexus_token')
    localStorage.removeItem('apexus_user')
    window.location.href = '/login'
    return
  }

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    const msg = data.message || data.error || `Erro ${res.status}`
    throw new Error(msg)
  }

  return data
}

// Auth
export const auth = {
  login: (email, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
}

// Candidates
export const candidates = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/candidates${qs ? `?${qs}` : ''}`)
  },
  get: (id) => request(`/candidates/${id}`),
  create: (data) =>
    request('/candidates', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) =>
    request(`/candidates/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id) => request(`/candidates/${id}`, { method: 'DELETE' }),
}

// Interviews
export const interviews = {
  list: () => request('/interviews'),
  get: (id) => request(`/interviews/${id}`),
  assessments: (id) => request(`/interviews/${id}/assessments`),
}

// Analytics
export const analytics = {
  overview: () => request('/analytics/overview'),
  pipeline: () => request('/analytics/pipeline'),
  performance: () => request('/analytics/performance'),
}

// Reports
export const reports = {
  candidates: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/reports/candidates${qs ? `?${qs}` : ''}`)
  },
}

// Health
export const health = {
  metrics: () => request('/health/metrics'),
}
