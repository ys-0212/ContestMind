import { createClient } from './supabase'

const ENV_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"
const API_BASE_URL = ENV_URL.endsWith('/api/v1') ? ENV_URL : `${ENV_URL}/api/v1`

const supabase = createClient()

export const apiClient = {
  async getAuthHeaders() {
    const { data: { session } } = await supabase.auth.getSession()
    const headers = { 'Content-Type': 'application/json' }
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`
    }
    return headers
  },

  async get(endpoint) {
    const headers = await this.getAuthHeaders()
    const res = await fetch(`${API_BASE_URL}${endpoint}`, { headers })
    if (!res.ok) throw new Error(`API Error ${res.status}: ${res.statusText}`)
    return res.json()
  },

  async post(endpoint, data) {
    const headers = await this.getAuthHeaders()
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error(`API Error ${res.status}: ${res.statusText}`)
    return res.json()
  },

  // --- Profile & Analytics ---

  async getProfile(handle) {
    return this.get(`/profiles/${handle}`)
  },

  async getAnalytics(handle) {
    return this.get(`/analytics/weaknesses?handle=${handle}`)
  },

  async getHistory(handle) {
    return this.get(`/profiles/${handle}/rating`)
  },

  async getSubmissions(handle, limit = 10) {
    return this.get(`/profiles/${handle}/submissions?limit=${limit}`)
  },

  // --- Problems ---

  async getProblems(tags = "") {
    const data = await this.get(`/problems?limit=50${tags ? `&tags=${tags}` : ''}`)
    if (data?.result?.problems) {
      data.result.problems = data.result.problems.map(p => ({
        ...p,
        problem_id: p.problem_id || (p.contestId && p.index ? `${p.contestId}${p.index}` : String(Math.random())),
        title: p.name || p.title || '',
      }))
    }
    return data
  },

  async getProblem(id) {
    const data = await this.get(`/problems/${id}`)
    if (data) {
      data.problem_id = data.problem_id || (data.contestId && data.index ? `${data.contestId}${data.index}` : id)
      data.title = data.title || data.name || ''
    }
    return data
  },

  // --- Search ---

  async searchProblems(query) {
    return this.post('/retrieval/search', { query, top_k: 10 })
  },

  // --- Recommendations ---

  async getRecommendations(handle, count = 5) {
    return this.get(`/recommendations/?handle=${handle}&count=${count}`)
  },

  // --- Probability ---

  async getProbability(handle, problemId) {
    return this.get(`/probability/${handle}/${problemId}`)
  },

  // --- Hints ---

  async getHints(problemId, hintLevel, previousHints = []) {
    return this.post('/llm/hints', {
      problem_id: problemId,
      current_hint_level: hintLevel,
      previous_hints: previousHints,
    })
  },

  async recordHint(handle, problemId, hintLevel) {
    return this.post('/hints/', { handle, problem_id: problemId, hint_level: hintLevel })
  },

  async getMaxHintLevel(handle, problemId) {
    return this.get(`/hints/${handle}/${problemId}`)
  },

  // --- Chat ---

  async sendChatMessage(handle, problemId, message, codeContext = "") {
    const fullQuery = `[Problem: ${problemId}]\n[Code:\n${codeContext.slice(0, 1500)}]\n\nUser: ${message}`
    return this.post('/chat/ask', { query: fullQuery, handle })
  },

  // --- Code Execution (Piston → local subprocess fallback) ---

  async executeCode({ code, language, stdin = "", expected_output }) {
    const body = { code, language, stdin }
    if (expected_output !== undefined) body.expected_output = expected_output
    return this.post('/execute/', body)
  },
}
