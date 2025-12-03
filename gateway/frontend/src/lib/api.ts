import axios from 'axios'
import { useAuthStore } from '../store/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth
export const login = async (username: string, password: string) => {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)

  const response = await api.post('/admin/token', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data
}

// Provisioning
export const getOperations = async (params?: { account_id?: string; status?: string }) => {
  const response = await api.get('/provision/', { params })
  return response.data
}

export const getOperation = async (id: string) => {
  const response = await api.get(`/provision/${id}`)
  return response.data
}

export const createProvisioningRequest = async (data: any) => {
  const response = await api.post('/provision/', data)
  return response.data
}

export const rollbackOperation = async (id: string) => {
  const response = await api.post(`/provision/${id}/rollback`)
  return response.data
}

// Rules
export const getRules = async (params?: { target_system?: string; rule_type?: string }) => {
  const response = await api.get('/rules/', { params })
  return response.data
}

export const getRule = async (id: string) => {
  const response = await api.get(`/rules/${id}`)
  return response.data
}

export const createRule = async (data: any) => {
  const response = await api.post('/rules/', data)
  return response.data
}

export const updateRule = async (id: string, data: any) => {
  const response = await api.put(`/rules/${id}`, data)
  return response.data
}

export const deleteRule = async (id: string) => {
  const response = await api.delete(`/rules/${id}`)
  return response.data
}

export const testRule = async (ruleId: string, testData: any) => {
  const response = await api.post('/rules/test', { rule_id: ruleId, test_data: testData })
  return response.data
}

// Workflows
export const getWorkflowConfigs = async () => {
  const response = await api.get('/workflow/configs')
  return response.data
}

export const getWorkflowInstances = async (params?: { status?: string }) => {
  const response = await api.get('/workflow/instances', { params })
  return response.data
}

export const getPendingApprovals = async () => {
  const response = await api.get('/workflow/instances/pending')
  return response.data
}

export const approveWorkflow = async (instanceId: string, comments?: string) => {
  const response = await api.post(`/workflow/instances/${instanceId}/approve`, {
    workflow_instance_id: instanceId,
    decision: 'approved',
    comments,
  })
  return response.data
}

export const rejectWorkflow = async (instanceId: string, comments: string) => {
  const response = await api.post(`/workflow/instances/${instanceId}/reject`, {
    workflow_instance_id: instanceId,
    decision: 'rejected',
    comments,
  })
  return response.data
}

// Reconciliation
export const startReconciliation = async (targetSystems?: string[], fullSync?: boolean) => {
  const response = await api.post('/reconcile/start', {
    target_systems: targetSystems,
    full_sync: fullSync,
  })
  return response.data
}

export const getReconciliationStatus = async (jobId: string) => {
  const response = await api.get(`/reconcile/status/${jobId}`)
  return response.data
}

export const getReconciliationJobs = async () => {
  const response = await api.get('/reconcile/jobs')
  return response.data
}

export const getDiscrepancies = async (jobId: string) => {
  const response = await api.get(`/reconcile/${jobId}/discrepancies`)
  return response.data
}

// AI Assistant
export const queryAI = async (query: string, context?: any, conversationId?: string) => {
  const response = await api.post('/ai/query', {
    query,
    context,
    conversation_id: conversationId,
  })
  return response.data
}

export const suggestMappings = async (sourceSchema: any, targetSystem: string) => {
  const response = await api.post('/ai/suggest-mappings', {
    source_schema: sourceSchema,
    target_system: targetSystem,
  })
  return response.data
}

// Admin
export const getSystemStatus = async () => {
  const response = await api.get('/admin/status')
  return response.data
}

export const emergencyStop = async () => {
  const response = await api.post('/admin/emergency-stop')
  return response.data
}

export const resumeProvisioning = async () => {
  const response = await api.post('/admin/resume')
  return response.data
}

export const getConnectorsStatus = async () => {
  const response = await api.get('/admin/connectors/status')
  return response.data
}

export const getMetrics = async () => {
  const response = await api.get('/admin/metrics')
  return response.data
}

// Audit
export const searchAuditLogs = async (params: any) => {
  const response = await api.post('/admin/audit/search', params)
  return response.data
}

export const getRecentAuditLogs = async (limit?: number) => {
  const response = await api.get('/admin/audit/recent', { params: { limit } })
  return response.data
}

export default api
