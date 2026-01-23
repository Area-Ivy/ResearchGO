// API Configuration
// 是否使用 API 网关（Traefik）
const USE_GATEWAY = import.meta.env.VITE_USE_GATEWAY === 'false'

// API 网关地址
export const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8080'

// 旧版单体服务地址（兼容）
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 微服务配置 - 根据是否使用网关自动切换
export const AUTH_SERVICE_URL = USE_GATEWAY ? GATEWAY_URL : (import.meta.env.VITE_AUTH_SERVICE_URL || 'http://localhost:8001')
export const CONVERSATION_SERVICE_URL = USE_GATEWAY ? GATEWAY_URL : (import.meta.env.VITE_CONVERSATION_SERVICE_URL || 'http://localhost:8002')
export const PAPER_STORAGE_SERVICE_URL = USE_GATEWAY ? GATEWAY_URL : (import.meta.env.VITE_PAPER_STORAGE_SERVICE_URL || 'http://localhost:8003')
export const VECTOR_SEARCH_SERVICE_URL = USE_GATEWAY ? GATEWAY_URL : (import.meta.env.VITE_VECTOR_SEARCH_SERVICE_URL || 'http://localhost:8004')
export const LITERATURE_SERVICE_URL = USE_GATEWAY ? GATEWAY_URL : (import.meta.env.VITE_LITERATURE_SERVICE_URL || 'http://localhost:8005')
export const CHAT_SERVICE_URL = USE_GATEWAY ? GATEWAY_URL : (import.meta.env.VITE_CHAT_SERVICE_URL || 'http://localhost:8006')
export const MINDMAP_SERVICE_URL = USE_GATEWAY ? GATEWAY_URL : (import.meta.env.VITE_MINDMAP_SERVICE_URL || 'http://localhost:8007')
export const ANALYSIS_SERVICE_URL = USE_GATEWAY ? GATEWAY_URL : (import.meta.env.VITE_ANALYSIS_SERVICE_URL || 'http://localhost:8008')
export const AGENT_SERVICE_URL = USE_GATEWAY ? GATEWAY_URL : (import.meta.env.VITE_AGENT_SERVICE_URL || 'http://localhost:8000')

export const API_ENDPOINTS = {
  CHAT_MESSAGE: `${CHAT_SERVICE_URL}/api/chat/message`,
  CHAT_HEALTH: `${CHAT_SERVICE_URL}/api/chat/health`,
  AGENT_CHAT: `${AGENT_SERVICE_URL}/api/agent/chat`,
  AGENT_TOOLS: `${AGENT_SERVICE_URL}/api/agent/tools`
}

// 默认导出（兼容性）
export default {
  apiBaseUrl: API_BASE_URL,
  gatewayUrl: GATEWAY_URL,
  useGateway: USE_GATEWAY,
  endpoints: API_ENDPOINTS
}

