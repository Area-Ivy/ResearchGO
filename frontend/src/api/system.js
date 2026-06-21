import { AGENT_SERVICE_URL } from '../config'
import { createServiceClient } from './client'

const systemClient = createServiceClient(AGENT_SERVICE_URL)

export const getSystemStatus = async () => {
  const response = await systemClient.get('/api/system/status')
  return response.data
}
