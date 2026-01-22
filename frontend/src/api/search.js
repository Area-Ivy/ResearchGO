/**
 * 论文搜索 API - 调用向量搜索服务
 */
import axios from 'axios'
import { VECTOR_SEARCH_SERVICE_URL } from '../config'

// 创建向量搜索服务专用的axios实例
const vectorSearchClient = axios.create({
  baseURL: VECTOR_SEARCH_SERVICE_URL
})

// 请求拦截器：自动添加token
vectorSearchClient.interceptors.request.use(
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
vectorSearchClient.interceptors.response.use(
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
 * 语义搜索论文
 * @param {string} query - 搜索查询
 * @param {number} topK - 返回结果数量
 * @param {string} uploadedAfter - 过滤上传时间（ISO格式）
 * @returns {Promise} 搜索结果
 */
export async function semanticSearch(query, topK = 10, uploadedAfter = null) {
  try {
    const response = await vectorSearchClient.post('/api/vector/search', {
      query,
      top_k: topK,
      uploaded_after: uploadedAfter
    })
    return response.data
  } catch (error) {
    console.error('Semantic search failed:', error)
    throw error
  }
}

/**
 * 按论文分组搜索结果
 * @param {Array} results - 搜索结果数组
 * @returns {Object} 按paper_id分组的结果
 */
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
    
    // 更新最大相关性
    if (result.relevance_score > papers[paperId].max_relevance) {
      papers[paperId].max_relevance = result.relevance_score
    }
  }
  
  // 转换为数组并按相关性排序
  return Object.values(papers).sort((a, b) => b.max_relevance - a.max_relevance)
}

/**
 * 去重搜索结果（每篇论文最多保留N个chunks）
 * @param {Array} results - 搜索结果数组
 * @param {number} maxPerPaper - 每篇论文最多保留的chunk数
 * @returns {Array} 去重后的结果
 */
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

/**
 * 高亮搜索关键词
 * @param {string} text - 文本
 * @param {string} query - 查询词
 * @returns {string} 带高亮标记的HTML
 */
export function highlightQuery(text, query) {
  if (!query || !text) return text
  
  const keywords = query.split(/\s+/).filter(k => k.length > 0)
  let highlightedText = text
  
  for (const keyword of keywords) {
    const regex = new RegExp(`(${escapeRegex(keyword)})`, 'gi')
    highlightedText = highlightedText.replace(regex, '<mark>$1</mark>')
  }
  
  return highlightedText
}

/**
 * 转义正则表达式特殊字符
 */
function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 格式化相关性分数
 * @param {number} score - 相关性分数（0-1）
 * @returns {string} 格式化的百分比
 */
export function formatRelevance(score) {
  return `${(score * 100).toFixed(1)}%`
}

/**
 * 生成引用格式
 * @param {Object} result - 搜索结果
 * @returns {string} 引用文本
 */
export function generateCitation(result) {
  return `${result.file_name}, 第${result.chunk_index + 1}段, 页码${result.page_range}`
}

