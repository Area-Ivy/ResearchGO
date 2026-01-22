/**
 * 对话管理相关API
 */
import axios from 'axios'
import { CONVERSATION_SERVICE_URL } from '../config'

// 创建对话服务专用的axios实例
const conversationClient = axios.create({
  baseURL: CONVERSATION_SERVICE_URL
})

// 请求拦截器：自动添加token
conversationClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理401错误
conversationClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

/**
 * 创建新对话会话
 * @param {string} title - 对话标题
 * @returns {Promise<Object>} 对话会话信息
 */
export const createConversation = async (title) => {
  const response = await conversationClient.post('/api/conversations', { title })
  return response.data
}

/**
 * 获取对话会话列表
 * @param {number} skip - 跳过的记录数
 * @param {number} limit - 返回的记录数限制
 * @returns {Promise<Object>} 对话会话列表
 */
export const getConversations = async (skip = 0, limit = 50) => {
  const response = await conversationClient.get('/api/conversations', {
    params: { skip, limit }
  })
  return response.data
}

/**
 * 获取对话会话详情
 * @param {number} conversationId - 对话会话ID
 * @returns {Promise<Object>} 对话会话详情（包含消息）
 */
export const getConversation = async (conversationId) => {
  const response = await conversationClient.get(`/api/conversations/${conversationId}`)
  return response.data
}

/**
 * 更新对话会话
 * @param {number} conversationId - 对话会话ID
 * @param {string} title - 新标题
 * @returns {Promise<Object>} 更新后的对话会话信息
 */
export const updateConversation = async (conversationId, title) => {
  const response = await conversationClient.put(`/api/conversations/${conversationId}`, { title })
  return response.data
}

/**
 * 删除对话会话
 * @param {number} conversationId - 对话会话ID
 * @returns {Promise<void>}
 */
export const deleteConversation = async (conversationId) => {
  await conversationClient.delete(`/api/conversations/${conversationId}`)
}

/**
 * 向对话会话添加消息
 * @param {number} conversationId - 对话会话ID
 * @param {string} role - 角色（user 或 assistant）
 * @param {string} content - 消息内容
 * @returns {Promise<Object>} 创建的消息信息
 */
export const addMessage = async (conversationId, role, content) => {
  const response = await conversationClient.post(`/api/conversations/${conversationId}/messages`, {
    role,
    content
  })
  return response.data
}

/**
 * 获取对话会话的所有消息
 * @param {number} conversationId - 对话会话ID
 * @returns {Promise<Array>} 消息列表
 */
export const getMessages = async (conversationId) => {
  const response = await conversationClient.get(`/api/conversations/${conversationId}/messages`)
  return response.data
}

