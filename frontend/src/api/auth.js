/**
 * 认证相关API
 */
import axios from 'axios'
import { API_BASE_URL } from '../config'

/**
 * 创建带认证的axios实例
 */
const authAxios = axios.create({
  baseURL: API_BASE_URL
})

// 请求拦截器：自动添加token
authAxios.interceptors.request.use(
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
authAxios.interceptors.response.use(
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

/**
 * 用户登录
 * @param {Object} credentials - 登录凭据
 * @param {string} credentials.username - 用户名或邮箱
 * @param {string} credentials.password - 密码
 * @returns {Promise<Object>} 包含token和用户信息
 */
export const login = async (credentials) => {
  const response = await axios.post(`${API_BASE_URL}/api/auth/login`, credentials)
  return response.data
}

/**
 * 用户注册
 * @param {Object} userData - 用户注册数据
 * @param {string} userData.username - 用户名
 * @param {string} userData.email - 邮箱
 * @param {string} userData.password - 密码
 * @returns {Promise<Object>} 包含token和用户信息
 */
export const register = async (userData) => {
  const response = await axios.post(`${API_BASE_URL}/api/auth/register`, userData)
  return response.data
}

/**
 * 获取当前用户信息
 * @returns {Promise<Object>} 用户信息
 */
export const getCurrentUser = async () => {
  const response = await authAxios.get('/api/auth/me')
  return response.data
}

/**
 * 更新当前用户信息
 * @param {Object} userData - 要更新的用户数据
 * @returns {Promise<Object>} 更新后的用户信息
 */
export const updateCurrentUser = async (userData) => {
  const response = await authAxios.put('/api/auth/me', userData)
  return response.data
}

/**
 * 用户登出
 */
export const logout = async () => {
  try {
    await authAxios.post('/api/auth/logout')
  } finally {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }
}

/**
 * 检查是否已登录
 * @returns {boolean}
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('token')
}

/**
 * 获取存储的用户信息
 * @returns {Object|null}
 */
export const getStoredUser = () => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
}

export default authAxios

