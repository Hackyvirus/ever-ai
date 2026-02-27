import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE_URL, timeout: 120000 })

export const analyzeText = (text) =>
  api.post('/api/analyze/sync', { text }).then(r => r.data)

export const analyzeAsync = (text) =>
  api.post('/api/analyze', { text }).then(r => r.data)

export const getReport = (id) =>
  api.get(`/api/report/${id}`).then(r => r.data)

export const getHistory = () =>
  api.get('/api/history').then(r => r.data)

export const pollReport = async (queryId, onUpdate, maxWait = 120000) => {
  const start = Date.now()
  while (Date.now() - start < maxWait) {
    const result = await getReport(queryId)
    onUpdate(result)
    if (result.status === 'completed' || result.status === 'failed') return result
    await new Promise(r => setTimeout(r, 2000))
  }
  throw new Error('Analysis timed out')
}
