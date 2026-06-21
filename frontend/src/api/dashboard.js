import { AGENT_SERVICE_URL } from '../config'
import { createServiceClient } from './client'

const dashboardClient = createServiceClient(AGENT_SERVICE_URL)

export const getDashboardSummary = async () => {
  const response = await dashboardClient.get('/api/dashboard/summary')
  return response.data
}
