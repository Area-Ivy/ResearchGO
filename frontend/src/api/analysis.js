/**
 * Analysis API
 * 论文分析相关的API调用
 */
import axios from 'axios'
import { ANALYSIS_SERVICE_URL } from '../config'

// 创建分析服务专用的 axios 实例
const analysisClient = axios.create({
  baseURL: ANALYSIS_SERVICE_URL
})

// 请求拦截器：自动添加 token
analysisClient.interceptors.request.use(
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
 * 生成论文分析
 * @param {string} objectName - MinIO中的PDF对象名称
 * @param {string} language - 语言（zh/en）
 * @returns {Promise} API响应
 */
export async function generateAnalysis(objectName, language = 'zh') {
  try {
    const response = await analysisClient.post('/api/analysis/generate', {
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
    const response = await analysisClient.get('/api/analysis/health')
    return response.data
  } catch (error) {
    console.error('Error checking analysis service health:', error)
    throw error
  }
}

