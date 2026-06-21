import axios from 'axios'
import { API_BASE_URL } from '../config'

export function redirectToLogin() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')

  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export function createServiceClient(baseURL, options = {}) {
  const client = axios.create({
    baseURL,
    ...options
  })

  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        redirectToLogin()
      }
      return Promise.reject(error)
    }
  )

  return client
}

const apiClient = createServiceClient(API_BASE_URL)

export default apiClient
