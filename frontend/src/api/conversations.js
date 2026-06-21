import { CONVERSATION_SERVICE_URL } from '../config'
import { createServiceClient } from './client'

const conversationClient = createServiceClient(CONVERSATION_SERVICE_URL)

export const createConversation = async (title) => {
  const response = await conversationClient.post('/api/conversations', { title })
  return response.data
}

export const getConversations = async (skip = 0, limit = 50) => {
  const response = await conversationClient.get('/api/conversations', {
    params: { skip, limit }
  })
  return response.data
}

export const getConversation = async (conversationId) => {
  const response = await conversationClient.get(`/api/conversations/${conversationId}`)
  return response.data
}

export const updateConversation = async (conversationId, title) => {
  const response = await conversationClient.put(`/api/conversations/${conversationId}`, { title })
  return response.data
}

export const deleteConversation = async (conversationId) => {
  await conversationClient.delete(`/api/conversations/${conversationId}`)
}

export const addMessage = async (conversationId, role, content) => {
  const response = await conversationClient.post(`/api/conversations/${conversationId}/messages`, {
    role,
    content
  })
  return response.data
}

export const getMessages = async (conversationId) => {
  const response = await conversationClient.get(`/api/conversations/${conversationId}/messages`)
  return response.data
}
