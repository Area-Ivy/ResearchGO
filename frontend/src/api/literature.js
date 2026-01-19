/**
 * Literature Search API
 * Interfaces with backend OpenAlex API endpoints
 */
import { API_BASE_URL } from '../config'

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
    const response = await fetch(`${API_BASE_URL}/api/literature/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Search failed')
    }

    return await response.json()
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
    const response = await fetch(`${API_BASE_URL}/api/literature/work/${workId}`)

    if (!response.ok) {
      throw new Error('Failed to fetch work details')
    }

    return await response.json()
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
    const response = await fetch(
      `${API_BASE_URL}/api/literature/related/${workId}?limit=${limit}`
    )

    if (!response.ok) {
      throw new Error('Failed to fetch related works')
    }

    return await response.json()
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
    const response = await fetch(`${API_BASE_URL}/api/literature/author/${authorId}`)

    if (!response.ok) {
      throw new Error('Failed to fetch author info')
    }

    return await response.json()
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
    const response = await fetch(`${API_BASE_URL}/api/literature/summarize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ work_id: workId, language })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Summarization failed')
    }

    return await response.json()
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
    const response = await fetch(`${API_BASE_URL}/api/literature/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ work_ids: workIds, format })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Export failed')
    }

    return await response.json()
  } catch (error) {
    console.error('Export citations error:', error)
    throw error
  }
}

