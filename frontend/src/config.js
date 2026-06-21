// API Configuration
const normalizeBaseUrl = (value, fallback) => {
  if (value === undefined) return fallback
  if (value === '') return ''
  return value.replace(/\/+$/, '')
}

// Whether to use the API gateway (Traefik). Set VITE_USE_GATEWAY=false to disable it.
const USE_GATEWAY = import.meta.env.VITE_USE_GATEWAY !== 'false'

const DEFAULT_GATEWAY_URL = import.meta.env.PROD ? '' : 'http://localhost:8080'

// API gateway address
export const GATEWAY_URL = normalizeBaseUrl(
  import.meta.env.VITE_GATEWAY_URL,
  DEFAULT_GATEWAY_URL
)

// Legacy monolith API base URL
export const API_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_API_BASE_URL,
  'http://localhost:8000'
)

const resolveServiceUrl = (envValue, fallback) => (
  USE_GATEWAY ? GATEWAY_URL : normalizeBaseUrl(envValue, fallback)
)

// Microservice configuration. Switch automatically based on gateway usage.
export const AUTH_SERVICE_URL = resolveServiceUrl(import.meta.env.VITE_AUTH_SERVICE_URL, 'http://localhost:8001')
export const CONVERSATION_SERVICE_URL = resolveServiceUrl(import.meta.env.VITE_CONVERSATION_SERVICE_URL, 'http://localhost:8002')
export const PAPER_STORAGE_SERVICE_URL = resolveServiceUrl(import.meta.env.VITE_PAPER_STORAGE_SERVICE_URL, 'http://localhost:8003')
export const VECTOR_SEARCH_SERVICE_URL = resolveServiceUrl(import.meta.env.VITE_VECTOR_SEARCH_SERVICE_URL, 'http://localhost:8004')
export const LITERATURE_SERVICE_URL = resolveServiceUrl(import.meta.env.VITE_LITERATURE_SERVICE_URL, 'http://localhost:8005')
export const MINDMAP_SERVICE_URL = resolveServiceUrl(import.meta.env.VITE_MINDMAP_SERVICE_URL, 'http://localhost:8007')
export const ANALYSIS_SERVICE_URL = resolveServiceUrl(import.meta.env.VITE_ANALYSIS_SERVICE_URL, 'http://localhost:8008')
export const AGENT_SERVICE_URL = resolveServiceUrl(import.meta.env.VITE_AGENT_SERVICE_URL, 'http://localhost:8000')

export const API_ENDPOINTS = {
  AGENT_CHAT: `${AGENT_SERVICE_URL}/api/agent/chat`,
  AGENT_TOOLS: `${AGENT_SERVICE_URL}/api/agent/tools`
}

export default {
  apiBaseUrl: API_BASE_URL,
  gatewayUrl: GATEWAY_URL,
  useGateway: USE_GATEWAY,
  endpoints: API_ENDPOINTS
}
