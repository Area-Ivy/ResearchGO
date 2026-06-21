import axios from 'axios'
import { AUTH_SERVICE_URL } from '../config'
import { createServiceClient, redirectToLogin } from './client'

const authAxios = createServiceClient(AUTH_SERVICE_URL)

export const login = async (credentials) => {
  const response = await axios.post(`${AUTH_SERVICE_URL}/api/auth/login`, credentials)
  return response.data
}

export const register = async (userData) => {
  const response = await axios.post(`${AUTH_SERVICE_URL}/api/auth/register`, userData)
  return response.data
}

export const getCurrentUser = async () => {
  const response = await authAxios.get('/api/auth/me')
  return response.data
}

export const updateCurrentUser = async (userData) => {
  const response = await authAxios.put('/api/auth/me', userData)
  return response.data
}

export const logout = async () => {
  try {
    await authAxios.post('/api/auth/logout')
  } finally {
    redirectToLogin()
  }
}

export const isAuthenticated = () => {
  return !!localStorage.getItem('token')
}

export const getStoredUser = () => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
}

export default authAxios
