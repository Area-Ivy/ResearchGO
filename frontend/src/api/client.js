/**
 * API客户端配置
 */
import axios from 'axios'
import { API_BASE_URL } from '../config'

/**
 * 创建带认证的axios实例（用于调用单体服务）
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL
})

// 请求拦截器：自动添加token
apiClient.interceptors.request.use(
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
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token过期或无效，清除本地存储并跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient

