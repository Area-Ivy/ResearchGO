/**
 * 对话管理相关API
 */
import authAxios from './auth'

/**
 * 创建新对话会话
 * @param {string} title - 对话标题
 * @returns {Promise<Object>} 对话会话信息
 */
export const createConversation = async (title) => {
  const response = await authAxios.post('/api/conversations', { title })
  return response.data
}

/**
 * 获取对话会话列表
 * @param {number} skip - 跳过的记录数
 * @param {number} limit - 返回的记录数限制
 * @returns {Promise<Object>} 对话会话列表
 */
export const getConversations = async (skip = 0, limit = 50) => {
  const response = await authAxios.get('/api/conversations', {
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
  const response = await authAxios.get(`/api/conversations/${conversationId}`)
  return response.data
}

/**
 * 更新对话会话
 * @param {number} conversationId - 对话会话ID
 * @param {string} title - 新标题
 * @returns {Promise<Object>} 更新后的对话会话信息
 */
export const updateConversation = async (conversationId, title) => {
  const response = await authAxios.put(`/api/conversations/${conversationId}`, { title })
  return response.data
}

/**
 * 删除对话会话
 * @param {number} conversationId - 对话会话ID
 * @returns {Promise<void>}
 */
export const deleteConversation = async (conversationId) => {
  await authAxios.delete(`/api/conversations/${conversationId}`)
}

/**
 * 向对话会话添加消息
 * @param {number} conversationId - 对话会话ID
 * @param {string} role - 角色（user 或 assistant）
 * @param {string} content - 消息内容
 * @returns {Promise<Object>} 创建的消息信息
 */
export const addMessage = async (conversationId, role, content) => {
  const response = await authAxios.post(`/api/conversations/${conversationId}/messages`, {
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
  const response = await authAxios.get(`/api/conversations/${conversationId}/messages`)
  return response.data
}

