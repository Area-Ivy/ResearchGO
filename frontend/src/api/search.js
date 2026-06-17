import { VECTOR_SEARCH_SERVICE_URL } from '../config'
import { createServiceClient } from './client'

const vectorSearchClient = createServiceClient(VECTOR_SEARCH_SERVICE_URL)

export async function semanticSearch(query, topK = null, uploadedAfter = null) {
  try {
    const payload = {
      query,
      uploaded_after: uploadedAfter
    }
    if (topK !== null && topK !== undefined) {
      payload.top_k = topK
    }
    const response = await vectorSearchClient.post('/api/vector/search', payload)
    return response.data
  } catch (error) {
    console.error('Semantic search failed:', error)
    throw error
  }
}

export function groupResultsByPaper(results) {
  const papers = {}

  for (const result of results) {
    const paperId = result.paper_id

    if (!papers[paperId]) {
      papers[paperId] = {
        paper_id: paperId,
        file_name: result.file_name,
        title: result.title,
        upload_time: result.upload_time,
        chunks: [],
        max_relevance: result.relevance_score
      }
    }

    papers[paperId].chunks.push({
      chunk_id: result.chunk_id,
      chunk_index: result.chunk_index,
      content: result.content,
      chunk_chars: result.chunk_chars,
      page_range: result.page_range,
      relevance_score: result.relevance_score,
      distance: result.distance
    })

    if (result.relevance_score > papers[paperId].max_relevance) {
      papers[paperId].max_relevance = result.relevance_score
    }
  }

  return Object.values(papers).sort((a, b) => b.max_relevance - a.max_relevance)
}

export function deduplicateResults(results, maxPerPaper = 3) {
  const paperCounts = {}
  const deduplicated = []

  for (const result of results) {
    const paperId = result.paper_id
    const count = paperCounts[paperId] || 0

    if (count < maxPerPaper) {
      deduplicated.push(result)
      paperCounts[paperId] = count + 1
    }
  }

  return deduplicated
}

export function highlightQuery(text, query) {
  if (!query || !text) return text

  const keywords = query.split(/\s+/).filter((keyword) => keyword.length > 0)
  let highlightedText = text

  for (const keyword of keywords) {
    const regex = new RegExp(`(${escapeRegex(keyword)})`, 'gi')
    highlightedText = highlightedText.replace(regex, '<mark>$1</mark>')
  }

  return highlightedText
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function formatRelevance(score) {
  return `${(score * 100).toFixed(1)}%`
}

export function generateCitation(result) {
  const chunkNumber = Number.isFinite(result.chunk_index) ? result.chunk_index + 1 : ''
  const pageRange = result.page_range ? ` pages ${result.page_range}` : ''
  return `${result.file_name}, chunk ${chunkNumber}${pageRange}`
}
