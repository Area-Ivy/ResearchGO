import { VECTOR_SEARCH_SERVICE_URL } from '../config'
import { createServiceClient } from './client'

const retrievalSettingsClient = createServiceClient(VECTOR_SEARCH_SERVICE_URL)

export const getRetrievalSettings = async () => {
  const response = await retrievalSettingsClient.get('/api/vector/settings')
  return response.data
}

export const updateRetrievalSettings = async (settings) => {
  const response = await retrievalSettingsClient.put('/api/vector/settings', settings)
  return response.data
}
