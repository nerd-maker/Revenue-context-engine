import axios from 'axios'
import toast from 'react-hot-toast'

// Create axios instance
const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }

        // Add tenant ID from localStorage
        const tenantId = localStorage.getItem('tenant_id')
        if (tenantId) {
            config.headers['X-Tenant-ID'] = tenantId
        }

        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor - handle errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            const { status, data } = error.response

            // Handle specific error codes
            if (status === 401) {
                // Unauthorized - clear auth and redirect to login
                localStorage.removeItem('auth_token')
                localStorage.removeItem('tenant_id')
                window.location.href = '/login'
                toast.error('Session expired. Please login again.')
            } else if (status === 403) {
                toast.error('You do not have permission to perform this action.')
            } else if (status === 429) {
                toast.error('Too many requests. Please slow down.')
            } else if (status >= 500) {
                toast.error('Server error. Please try again later.')
            } else if (data?.detail) {
                toast.error(data.detail)
            }
        } else if (error.request) {
            toast.error('Network error. Please check your connection.')
        }

        return Promise.reject(error)
    }
)

// API methods
export const accountsApi = {
    list: (params) => api.get('/accounts', { params }),
    get: (id) => api.get(`/accounts/${id}`),
    getSignals: (id) => api.get(`/accounts/${id}/signals`),
    getActions: (id) => api.get(`/accounts/${id}/actions`),
}

export const actionsApi = {
    list: (params) => api.get('/actions', { params }),
    get: (id) => api.get(`/actions/${id}`),
    approve: (id) => api.post(`/actions/${id}/approve`),
    reject: (id, reason) => api.post(`/actions/${id}/reject`, { reason }),
    update: (id, data) => api.patch(`/actions/${id}`, data),
    bulkApprove: (ids) => api.post('/actions/bulk-approve', { action_ids: ids }),
}

export const signalsApi = {
    list: (params) => api.get('/signals', { params }),
    create: (data) => api.post('/signals', data),
    recent: (hours = 24) => api.get('/signals/recent', { params: { hours } }),
}

export const metricsApi = {
    summary: () => api.get('/metrics/summary'),
}

export const analyticsApi = {
    signals: (params) => api.get('/analytics/signals', { params }),
    intentScores: (params) => api.get('/analytics/intent-scores', { params }),
    actions: (params) => api.get('/analytics/actions', { params }),
}

export const settingsApi = {
    get: () => api.get('/settings'),
    updateICP: (data) => api.put('/settings/icp', data),
    updateBrandVoice: (data) => api.put('/settings/brand-voice', data),
    updateSignalWeights: (data) => api.put('/settings/signal-weights', data),
}

export const integrationsApi = {
    getSalesforceAuthUrl: () => api.get('/integrations/salesforce/auth-url'),
    testSalesforce: () => api.post('/integrations/salesforce/test'),
    updateOutreach: (apiKey) => api.put('/integrations/outreach', { api_key: apiKey }),
    updateClearbit: (apiKey) => api.put('/integrations/clearbit', { api_key: apiKey }),
}

export const promptsApi = {
    list: () => api.get('/prompts'),
    createVersion: (name, data) => api.post(`/prompts/${name}/versions`, data),
    activateVersion: (name, version) => api.post(`/prompts/${name}/versions/${version}/activate`),
}

export const usersApi = {
    list: () => api.get('/users'),
    invite: (email, role) => api.post('/users/invite', { email, role }),
    updateRole: (id, role) => api.put(`/users/${id}/role`, { role }),
}

export default api
