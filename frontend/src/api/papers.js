import { PAPER_STORAGE_SERVICE_URL, VECTOR_SEARCH_SERVICE_URL } from '../config'
import { createServiceClient } from './client'

const paperClient = createServiceClient(PAPER_STORAGE_SERVICE_URL)
const vectorClient = createServiceClient(VECTOR_SEARCH_SERVICE_URL)

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

export async function listPapers() {
  const response = await paperClient.get('/api/papers/list')
  return response.data
}

export async function getPaperStatus(objectName) {
  const response = await paperClient.get(`/api/papers/status/${objectName}`)
  return response.data
}

export async function renamePaper(objectName, originalName) {
  const response = await paperClient.patch(`/api/papers/rename/${objectName}`, {
    original_name: originalName
  })
  return response.data
}

export async function downloadPaper(objectName, originalName) {
  const response = await paperClient.get(
    `/api/papers/download/${objectName}`,
    { responseType: 'blob' }
  )

  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', originalName || objectName)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function deletePaper(objectName) {
  const response = await paperClient.delete(`/api/papers/delete/${objectName}`)
  return response.data
}

export async function checkHealth() {
  const response = await paperClient.get('/api/papers/health')
  return response.data
}

export async function paperQA(paperId, question, chatHistory = [], topK = null) {
  const payload = {
    paper_id: paperId,
    question,
    chat_history: chatHistory
  }
  if (topK !== null && topK !== undefined) {
    payload.top_k = topK
  }
  const response = await vectorClient.post('/api/vector/qa', payload)
  return response.data
}
