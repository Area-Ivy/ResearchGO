import { AGENT_SERVICE_URL } from '../config'
import { createServiceClient } from './client'

const memoryClient = createServiceClient(AGENT_SERVICE_URL)

export const getMemoryDocument = async () => {
  const response = await memoryClient.get('/api/memory')
  return response.data
}

export const saveMemoryDocument = async (content) => {
  const response = await memoryClient.put('/api/memory', { content })
  return response.data
}

export const clearMemoryDocument = async () => {
  const response = await memoryClient.delete('/api/memory')
  return response.data
}
