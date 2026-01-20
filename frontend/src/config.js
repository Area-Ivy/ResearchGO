// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const API_ENDPOINTS = {
  CHAT_MESSAGE: `${API_BASE_URL}/api/chat/message`,
  CHAT_HEALTH: `${API_BASE_URL}/api/chat/health`
}

// 默认导出（兼容性）
export default {
  apiBaseUrl: API_BASE_URL,
  endpoints: API_ENDPOINTS
}

