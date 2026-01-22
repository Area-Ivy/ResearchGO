/**
 * Mindmap API
 * 思维导图相关的API调用
 */
import axios from 'axios'
import { MINDMAP_SERVICE_URL } from '../config'

// 创建思维导图服务专用的 axios 实例
const mindmapClient = axios.create({
  baseURL: MINDMAP_SERVICE_URL
})

// 请求拦截器：自动添加 token
mindmapClient.interceptors.request.use(
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

/**
 * 生成思维导图
 * @param {string} objectName - MinIO中的PDF对象名称
 * @param {number} maxDepth - 最大深度
 * @param {string} language - 语言（zh/en）
 * @returns {Promise} API响应
 */
export async function generateMindmap(objectName, maxDepth = 3, language = 'zh') {
  try {
    const response = await mindmapClient.post('/api/mindmap/generate', {
      object_name: objectName,
      max_depth: maxDepth,
      language: language
    })
    return response.data
  } catch (error) {
    console.error('Error generating mindmap:', error)
    throw error
  }
}

/**
 * 健康检查
 * @returns {Promise} 健康状态
 */
export async function healthCheck() {
  try {
    const response = await mindmapClient.get('/api/mindmap/health')
    return response.data
  } catch (error) {
    console.error('Error checking mindmap service health:', error)
    throw error
  }
}

