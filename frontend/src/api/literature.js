/**
 * Literature Search API
 * Interfaces with Literature Search Service (port 8005)
 */
import axios from 'axios'
import { LITERATURE_SERVICE_URL } from '../config'

// Create a dedicated axios instance for the literature service
const literatureClient = axios.create({
  baseURL: LITERATURE_SERVICE_URL
})

// Request interceptor: automatically add token
literatureClient.interceptors.request.use(
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

// Response interceptor: handle 401 errors
literatureClient.interceptors.response.use(
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
 * Search for academic works
 * @param {Object} params - Search parameters
 * @param {string} params.query - Search query
 * @param {Object} params.filters - Optional filters
 * @param {number} params.page - Page number
 * @param {number} params.per_page - Results per page
 * @param {string} params.sort - Sort order
 * @returns {Promise} Search results
 */
export async function searchWorks(params) {
  try {
    const response = await literatureClient.post('/api/literature/search', params)
    return response.data
  } catch (error) {
    console.error('Search works error:', error)
    throw error
  }
}

/**
 * Get detailed information about a work
 * @param {string} workId - OpenAlex work ID
 * @returns {Promise} Work details
 */
export async function getWorkDetail(workId) {
  try {
    const response = await literatureClient.get(`/api/literature/work/${workId}`)
    return response.data
  } catch (error) {
    console.error('Get work detail error:', error)
    throw error
  }
}

/**
 * Get related works
 * @param {string} workId - OpenAlex work ID
 * @param {number} limit - Maximum number of results
 * @returns {Promise} Related works
 */
export async function getRelatedWorks(workId, limit = 10) {
  try {
    const response = await literatureClient.get(`/api/literature/related/${workId}`, {
      params: { limit }
    })
    return response.data
  } catch (error) {
    console.error('Get related works error:', error)
    throw error
  }
}

/**
 * Get author information
 * @param {string} authorId - OpenAlex author ID
 * @returns {Promise} Author information
 */
export async function getAuthorInfo(authorId) {
  try {
    const response = await literatureClient.get(`/api/literature/author/${authorId}`)
    return response.data
  } catch (error) {
    console.error('Get author info error:', error)
    throw error
  }
}

/**
 * Generate AI summary of a work
 * @param {string} workId - OpenAlex work ID
 * @param {string} language - Summary language (zh/en)
 * @returns {Promise} Structured summary
 */
export async function summarizeWork(workId, language = 'zh') {
  try {
    const response = await literatureClient.post('/api/literature/summarize', {
      work_id: workId,
      language
    })
    return response.data
  } catch (error) {
    console.error('Summarize work error:', error)
    throw error
  }
}

/**
 * Export citations in various formats
 * @param {Array<string>} workIds - Array of work IDs
 * @param {string} format - Export format (bibtex/ris/apa/mla)
 * @returns {Promise} Export content
 */
export async function exportCitations(workIds, format = 'bibtex') {
  try {
    const response = await literatureClient.post('/api/literature/export', {
      work_ids: workIds,
      format
    })
    return response.data
  } catch (error) {
    console.error('Export citations error:', error)
    throw error
  }
}

