import { ANALYSIS_SERVICE_URL } from '../config'
import { createServiceClient } from './client'

const analysisClient = createServiceClient(ANALYSIS_SERVICE_URL)

export async function generateAnalysis(objectName, language = 'zh') {
  try {
    const response = await analysisClient.post('/api/analysis/generate', {
      object_name: objectName,
      language
    })
    return response.data
  } catch (error) {
    console.error('Error generating analysis:', error)
    throw error
  }
}

export async function healthCheck() {
  try {
    const response = await analysisClient.get('/api/analysis/health')
    return response.data
  } catch (error) {
    console.error('Error checking analysis service health:', error)
    throw error
  }
}
