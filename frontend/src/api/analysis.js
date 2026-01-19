/**
 * Analysis API
 * 论文分析相关的API调用
 */
import axios from 'axios'
import { API_BASE_URL } from '../config'

/**
 * 生成论文分析
 * @param {string} objectName - MinIO中的PDF对象名称
 * @param {string} language - 语言（zh/en）
 * @returns {Promise} API响应
 */
export async function generateAnalysis(objectName, language = 'zh') {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/analysis/generate`, {
      object_name: objectName,
      language: language
    })
    return response.data
  } catch (error) {
    console.error('Error generating analysis:', error)
    throw error
  }
}

/**
 * 健康检查
 * @returns {Promise} 健康状态
 */
export async function healthCheck() {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/analysis/health`)
    return response.data
  } catch (error) {
    console.error('Error checking analysis service health:', error)
    throw error
  }
}

