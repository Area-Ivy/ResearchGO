import { MINDMAP_SERVICE_URL } from '../config'
import { createServiceClient } from './client'

const mindmapClient = createServiceClient(MINDMAP_SERVICE_URL)

export async function generateMindmap(objectName, maxDepth = 3, language = 'zh') {
  try {
    const response = await mindmapClient.post('/api/mindmap/generate', {
      object_name: objectName,
      max_depth: maxDepth,
      language
    })
    return response.data
  } catch (error) {
    console.error('Error generating mindmap:', error)
    throw error
  }
}

export async function healthCheck() {
  try {
    const response = await mindmapClient.get('/api/mindmap/health')
    return response.data
  } catch (error) {
    console.error('Error checking mindmap service health:', error)
    throw error
  }
}
