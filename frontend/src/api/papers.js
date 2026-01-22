/**
 * Papers API
 * 文献管理相关的 API 调用
 */
import axios from 'axios'
import { PAPER_STORAGE_SERVICE_URL, VECTOR_SEARCH_SERVICE_URL } from '../config'

// 创建论文服务专用的axios实例
const paperClient = axios.create({
  baseURL: PAPER_STORAGE_SERVICE_URL
})

// 请求拦截器：自动添加token
paperClient.interceptors.request.use(
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

// 响应拦截器：处理401错误
paperClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

/**
 * 上传论文文件
 * @param {File} file - PDF 文件
 * @returns {Promise} 上传结果
 */
export async function uploadPaper(file) {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await paperClient.post('/api/papers/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  
  return response.data
}

/**
 * 获取论文列表
 * @returns {Promise} 论文列表
 */
export async function listPapers() {
  const response = await paperClient.get('/api/papers/list')
  return response.data
}

/**
 * 下载论文
 * @param {string} objectName - MinIO 中的对象名称
 * @param {string} originalName - 原始文件名（用于保存）
 */
export async function downloadPaper(objectName, originalName) {
  const response = await paperClient.get(
    `/api/papers/download/${objectName}`,
    { responseType: 'blob' }
  )
  
  // 创建下载链接
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', originalName || objectName)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

/**
 * 删除论文
 * @param {string} objectName - MinIO 中的对象名称
 * @returns {Promise} 删除结果
 */
export async function deletePaper(objectName) {
  const response = await paperClient.delete(`/api/papers/delete/${objectName}`)
  return response.data
}

/**
 * 健康检查
 * @returns {Promise} 健康状态
 */
export async function checkHealth() {
  const response = await paperClient.get('/api/papers/health')
  return response.data
}

/**
 * 论文问答 - AI 助手（调用向量搜索服务）
 * @param {string} paperId - 论文ID
 * @param {string} question - 用户问题
 * @param {Array} chatHistory - 聊天历史 [{role: 'user'|'assistant', content: '...'}]
 * @param {number} topK - 检索相关内容数量
 * @returns {Promise} 问答结果
 */
export async function paperQA(paperId, question, chatHistory = [], topK = 10) {
  const token = localStorage.getItem('token')
  
  const response = await axios.post(
    `${VECTOR_SEARCH_SERVICE_URL}/api/vector/qa`,
    {
      paper_id: paperId,
      question: question,
      chat_history: chatHistory,
      top_k: topK
    },
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  )
  return response.data
}

