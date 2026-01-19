/**
 * Mindmap API
 * 思维导图相关的API调用
 */
import axios from 'axios'
import { API_BASE_URL } from '../config'

/**
 * 生成思维导图
 * @param {string} objectName - MinIO中的PDF对象名称
 * @param {number} maxDepth - 最大深度
 * @param {string} language - 语言（zh/en）
 * @returns {Promise} API响应
 */
export async function generateMindmap(objectName, maxDepth = 3, language = 'zh') {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/mindmap/generate`, {
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
    const response = await axios.get(`${API_BASE_URL}/api/mindmap/health`)
    return response.data
  } catch (error) {
    console.error('Error checking mindmap service health:', error)
    throw error
  }
}

