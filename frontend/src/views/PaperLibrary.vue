<template>
  <div class="paper-library">
    <!-- Header -->
    <div class="library-header">
      <div class="header-section">
        <h1 class="page-title">Paper Library</h1>
        <p class="page-subtitle">AI-powered semantic search for your research papers</p>
      </div>
      <div class="header-actions">
        <div class="search-container">
          <div class="search-box">
            <div class="search-icon-wrapper">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </div>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search papers with AI-powered semantic understanding..."
              class="search-input"
              @keyup.enter="handleSemanticSearch"
            />
            <button 
              v-if="searchQuery && !isSearching"
              @click="clearSearch"
              class="search-clear-btn"
              title="Clear search"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
            <button 
              @click="handleSemanticSearch"
              class="search-submit-btn"
              :disabled="!searchQuery || isSearching"
              title="Search"
            >
              <svg v-if="!isSearching" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
              <div v-else class="search-spinner"></div>
            </button>
          </div>
          <div class="search-hint">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
            <span>Press Enter or click search to find papers by meaning</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Search Results Info -->
    <div v-if="searchResults.length > 0" class="search-results-info">
      <div class="results-header">
        <h3>
          Search Results: "{{ lastSearchQuery }}"
          <span class="results-count">({{ uniquePapersCount }} {{ uniquePapersCount === 1 ? 'paper' : 'papers' }} matched)</span>
        </h3>
        <span class="search-time">Found in {{ searchTimeMs }}ms</span>
      </div>
      <button @click="clearSearchResults" class="clear-results-btn">
        Back to Library
      </button>
    </div>

    <!-- Hidden File Input -->
    <input
      ref="fileInput"
      type="file"
      accept=".pdf"
      @change="handleFileSelect"
      style="display: none"
    />

    <!-- Upload Status Messages -->
    <div v-if="uploadError" class="status-message error-message">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="15" y1="9" x2="9" y2="15"></line>
        <line x1="9" y1="9" x2="15" y2="15"></line>
      </svg>
      <span>{{ uploadError }}</span>
      <button @click="uploadError = null" class="dismiss-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
    <div v-if="uploadSuccess" class="status-message success-message">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
      </svg>
      <span>File uploaded successfully!</span>
      <button @click="uploadSuccess = false" class="dismiss-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <!-- Papers List or Search Results -->
    <div class="papers-section">
      <div class="section-header">
        <div class="section-title-wrapper">
          <h2>
            {{ searchResults.length > 0 ? 'Search Results' : 'Your Papers' }}
          </h2>
          <span v-if="searchResults.length === 0" class="papers-count">
            {{ filteredPapers.length }} {{ filteredPapers.length === 1 ? 'paper' : 'papers' }}
          </span>
        </div>
        <div class="section-actions">
          <button 
            v-if="searchResults.length === 0"
            @click="triggerFileInput" 
            class="upload-btn"
            :disabled="isUploading"
            title="Upload PDF"
          >
            <svg v-if="!isUploading" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <div v-else class="btn-spinner"></div>
            <span>{{ isUploading ? 'Uploading...' : 'Upload Paper' }}</span>
          </button>
          <button 
            v-if="papers.length > 0 && searchResults.length === 0" 
            @click="loadPapers" 
            class="refresh-btn" 
            title="Refresh library"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"></polyline>
              <polyline points="1 20 1 14 7 14"></polyline>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading || isSearching" class="loading-container">
        <div class="loading-spinner"></div>
        <p class="loading-text">{{ isSearching ? 'Searching...' : 'Loading papers...' }}</p>
      </div>

      <!-- Search Results (Aggregated by Paper) -->
      <div v-else-if="groupedSearchResults.length > 0" class="search-results-grid">
        <div
          v-for="paper in groupedSearchResults"
          :key="paper.paper_id"
          class="paper-result-card"
        >
          <!-- Header with Icon and Info -->
          <div class="paper-result-header">
            <div class="paper-doc-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
              </svg>
            </div>
            <div class="paper-result-info">
              <h4 class="paper-result-title">{{ paper.title }}</h4>
              <div class="paper-result-meta">
                <span class="meta-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                  {{ paper.file_name }}
                </span>
                <span class="meta-divider">•</span>
                <span class="meta-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                  {{ formatDate(paper.upload_time) }}
                </span>
                <span class="meta-divider">•</span>
                <span class="meta-item sections-count">
                  {{ paper.matched_chunks }} {{ paper.matched_chunks === 1 ? 'section' : 'sections' }}
                </span>
              </div>
            </div>
            <div class="relevance-indicator" :class="getRelevanceClass(paper.max_relevance)">
              <div class="relevance-circle">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </div>
              <span class="relevance-text">{{ formatRelevance(paper.max_relevance) }}</span>
            </div>
          </div>
          
          <!-- Preview Sections -->
          <div class="paper-preview">
            <div class="preview-header">
              <span class="preview-label">Top Matching Sections</span>
            </div>
            <div class="preview-sections">
              <div 
                v-for="(chunk, idx) in paper.top_chunks.slice(0, 2)" 
                :key="chunk.chunk_id"
                class="preview-section"
              >
                <div class="section-header">
                  <span class="section-badge">Section {{ chunk.chunk_index + 1 }}</span>
                  <span class="section-pages">Pages {{ chunk.page_range }}</span>
                </div>
                <p class="section-content">{{ truncate(chunk.content, 150) }}</p>
              </div>
            </div>
            <div v-if="paper.matched_chunks > 2" class="more-sections">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="1"></circle>
                <circle cx="19" cy="12" r="1"></circle>
                <circle cx="5" cy="12" r="1"></circle>
              </svg>
              {{ paper.matched_chunks - 2 }} more {{ paper.matched_chunks - 2 === 1 ? 'section' : 'sections' }}
            </div>
          </div>
          
          <!-- Actions Footer -->
          <div class="paper-result-actions">
            <button @click="viewPaper(paper)" class="result-action-btn btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              <span>View Paper</span>
            </button>
            <button @click="handleDownload(findPaperByPaperId(paper.paper_id))" class="result-action-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              <span>Download</span>
            </button>
            <button @click="copyPaperReference(paper)" class="result-action-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>Copy</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="papers.length === 0" class="empty-state">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
        </svg>
        <h3>No Papers Yet</h3>
        <p>Upload your first PDF to get started</p>
      </div>

      <!-- Papers Grid -->
      <div v-else-if="filteredPapers.length === 0" class="empty-state">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        <h3>No Results Found</h3>
        <p>Try a different search term or use AI Search</p>
      </div>

      <div v-else class="papers-grid" style="display: flex; flex-direction: column; gap: 16px; width: 100%;">
        <div
          v-for="paper in filteredPapers"
          :key="paper.object_name"
          class="paper-card"
        >
          <div class="paper-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
          </div>
          <div class="paper-info">
            <h4 class="paper-name" :title="paper.original_name">{{ paper.original_name }}</h4>
            <div class="paper-meta">
              <span class="paper-size">{{ formatFileSize(paper.size) }}</span>
              <span class="paper-date">{{ formatDate(paper.last_modified) }}</span>
            </div>
          </div>
          <div class="paper-actions">
            <button @click="handleDownload(paper)" class="action-btn download-btn" title="Download">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
            </button>
            <button @click="confirmDelete(paper)" class="action-btn delete-btn" title="Delete">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <transition name="modal">
      <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>Delete Paper</h3>
            <button @click="showDeleteModal = false" class="modal-close">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete this paper?</p>
            <p class="paper-name-preview">{{ paperToDelete?.original_name }}</p>
            <p class="warning-text">This action cannot be undone.</p>
          </div>
          <div class="modal-actions">
            <button @click="showDeleteModal = false" class="btn-secondary">Cancel</button>
            <button @click="handleDelete" class="btn-danger" :disabled="isDeleting">
              {{ isDeleting ? 'Deleting...' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { uploadPaper, listPapers, downloadPaper, deletePaper } from '../api/papers'
import { semanticSearch, groupResultsByPaper, formatRelevance, generateCitation } from '../api/search'

export default {
  name: 'PaperLibrary',
  data() {
    return {
      papers: [],
      searchQuery: '',
      isLoading: false,
      isUploading: false,
      isDeleting: false,
      uploadError: null,
      uploadSuccess: false,
      showDeleteModal: false,
      paperToDelete: null,
      // 搜索相关
      isSearching: false,
      searchResults: [],
      lastSearchQuery: '',
      searchTimeMs: 0
    }
  },
  computed: {
    filteredPapers() {
      // 如果有搜索结果，不显示papers列表
      if (this.searchResults.length > 0) {
        return []
      }
      
      // 始终显示所有论文（搜索只通过语义搜索进行）
      return this.papers
    },
    
    groupedSearchResults() {
      if (this.searchResults.length === 0) return []
      
      // 按paper_id分组
      const papersMap = {}
      
      for (const result of this.searchResults) {
        const paperId = result.paper_id
        
        if (!papersMap[paperId]) {
          papersMap[paperId] = {
            paper_id: paperId,
            file_name: result.file_name,
            title: result.title,
            upload_time: result.upload_time,
            matched_chunks: 0,
            max_relevance: result.relevance_score,
            top_chunks: []
          }
        }
        
        papersMap[paperId].matched_chunks++
        papersMap[paperId].top_chunks.push(result)
        
        // 更新最大相关性
        if (result.relevance_score > papersMap[paperId].max_relevance) {
          papersMap[paperId].max_relevance = result.relevance_score
        }
      }
      
      // 转换为数组并按最大相关性排序
      const papers = Object.values(papersMap)
      papers.sort((a, b) => b.max_relevance - a.max_relevance)
      
      return papers
    },
    
    uniquePapersCount() {
      return this.groupedSearchResults.length
    }
  },
  mounted() {
    this.loadPapers()
  },
  methods: {
    async loadPapers() {
      this.isLoading = true
      try {
        const response = await listPapers()
        this.papers = response.papers || []
      } catch (error) {
        console.error('Failed to load papers:', error)
      } finally {
        this.isLoading = false
      }
    },
    
    async handleSemanticSearch() {
      if (!this.searchQuery.trim()) return
      
      this.isSearching = true
      this.searchResults = []
      
      try {
        console.log('Performing semantic search:', this.searchQuery)
        const response = await semanticSearch(this.searchQuery, 20)
        
        this.searchResults = response.results || []
        this.lastSearchQuery = this.searchQuery
        this.searchTimeMs = response.search_time_ms || 0
        
        console.log(`Found ${this.searchResults.length} results in ${this.searchTimeMs}ms`)
        
        if (this.searchResults.length === 0) {
          this.uploadError = 'No results found. Try different keywords.'
          setTimeout(() => {
            this.uploadError = null
          }, 3000)
        }
      } catch (error) {
        console.error('Semantic search failed:', error)
        this.uploadError = error.response?.data?.detail || 'Search failed. Please try again.'
        setTimeout(() => {
          this.uploadError = null
        }, 5000)
      } finally {
        this.isSearching = false
      }
    },
    
    clearSearch() {
      this.searchQuery = ''
      this.searchResults = []
      this.lastSearchQuery = ''
    },
    
    clearSearchResults() {
      this.searchResults = []
      this.lastSearchQuery = ''
      this.searchQuery = ''
    },
    
    
    highlightContent(content) {
      if (!this.lastSearchQuery) return content
      
      // 简单的关键词高亮
      const keywords = this.lastSearchQuery.split(/\s+/).filter(k => k.length > 0)
      let highlighted = content
      
      for (const keyword of keywords) {
        const regex = new RegExp(`(${this.escapeRegex(keyword)})`, 'gi')
        highlighted = highlighted.replace(regex, '<mark>$1</mark>')
      }
      
      return highlighted
    },
    
    escapeRegex(str) {
      return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    },
    
    formatRelevance(score) {
      return formatRelevance(score)
    },
    
    getRelevanceClass(score) {
      if (score >= 0.8) return 'high'
      if (score >= 0.6) return 'medium'
      return 'low'
    },
    
    viewPaper(paper) {
      // 这里可以跳转到PDF查看器
      console.log('View paper:', paper.paper_id)
      // TODO: 实现PDF查看功能
      alert(`View paper: ${paper.file_name}\n${paper.matched_chunks} relevant sections found\nBest match: ${this.formatRelevance(paper.max_relevance)}`)
    },
    
    findPaperByPaperId(paperId) {
      // 根据paper_id查找原始paper对象
      return this.papers.find(p => p.object_name === paperId) || { object_name: paperId, original_name: paperId }
    },
    
    copyPaperReference(paper) {
      const citation = `${paper.file_name} (${paper.matched_chunks} relevant sections, max relevance: ${this.formatRelevance(paper.max_relevance)})`
      navigator.clipboard.writeText(citation).then(() => {
        this.uploadSuccess = true
        setTimeout(() => {
          this.uploadSuccess = false
        }, 2000)
      }).catch(err => {
        console.error('Failed to copy:', err)
      })
    },
    
    truncate(text, maxLength) {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    },
    triggerFileInput() {
      if (!this.isUploading) {
        this.$refs.fileInput.click()
      }
    },
    handleFileSelect(event) {
      const file = event.target.files[0]
      if (file) {
        this.uploadFile(file)
      }
      // Reset input
      event.target.value = ''
    },
    async uploadFile(file) {
      this.isUploading = true
      this.uploadError = null
      this.uploadSuccess = false

      try {
        await uploadPaper(file)
        this.uploadSuccess = true
        setTimeout(() => {
          this.uploadSuccess = false
        }, 3000)
        // Reload papers list
        await this.loadPapers()
      } catch (error) {
        console.error('Upload failed:', error)
        this.uploadError = error.response?.data?.detail || 'Failed to upload file'
        setTimeout(() => {
          this.uploadError = null
        }, 5000)
      } finally {
        this.isUploading = false
      }
    },
    async handleDownload(paper) {
      try {
        await downloadPaper(paper.object_name, paper.original_name)
      } catch (error) {
        console.error('Download failed:', error)
        alert('Failed to download file')
      }
    },
    confirmDelete(paper) {
      this.paperToDelete = paper
      this.showDeleteModal = true
    },
    async handleDelete() {
      if (!this.paperToDelete) return

      this.isDeleting = true
      try {
        await deletePaper(this.paperToDelete.object_name)
        this.showDeleteModal = false
        this.paperToDelete = null
        // Reload papers list
        await this.loadPapers()
      } catch (error) {
        console.error('Delete failed:', error)
        alert('Failed to delete file')
      } finally {
        this.isDeleting = false
      }
    },
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    },
    formatDate(dateString) {
      if (!dateString) return 'Unknown'
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`
      
      return date.toLocaleDateString()
    }
  }
}
</script>

<script setup>
// Composition API setup (for keep-alive)
</script>

<style scoped>
.paper-library {
  max-width: 1600px;
  margin: 0 auto;
}

.library-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  gap: 24px;
}

.header-section {
  flex: 1;
}

.header-actions {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

/* Search Container */
.search-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 600px;
  width: 100%;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  padding: 0;
  overflow: hidden;
  transition: all 0.3s ease;
}

.search-box:focus-within {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
}

.search-icon-wrapper {
  padding: 0 16px;
  display: flex;
  align-items: center;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 14px;
  padding: 14px 8px;
  min-width: 0;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.search-clear-btn {
  padding: 8px;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.search-clear-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.search-submit-btn {
  padding: 14px 20px;
  background: var(--gradient-primary);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.search-submit-btn:hover:not(:disabled) {
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
  transform: translateY(-1px);
}

.search-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.search-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Search Hint */
.search-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
  padding-left: 4px;
}

.search-hint svg {
  color: var(--accent-primary);
  opacity: 0.7;
}

/* Status Messages */
.status-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-radius: 12px;
  margin-bottom: 24px;
  font-size: 14px;
  font-weight: 500;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.error-message {
  background: rgba(255, 107, 157, 0.1);
  border: 1px solid var(--accent-danger);
  color: var(--accent-danger);
}

.success-message {
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid var(--accent-success);
  color: var(--accent-success);
}

.status-message svg {
  flex-shrink: 0;
}

.status-message span {
  flex: 1;
}

.dismiss-btn {
  padding: 4px;
  background: none;
  border: none;
  color: currentColor;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.3s ease;
  display: flex;
  align-items: center;
  border-radius: 4px;
}

.dismiss-btn:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
}

/* Papers Section */
.papers-section {
  margin-bottom: 48px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-primary);
}

.section-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.papers-count {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border-primary);
}

.section-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* Upload Button */
.upload-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 10px;
  background: var(--gradient-primary);
  border: none;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
  white-space: nowrap;
}

.upload-btn:hover:not(:disabled) {
  box-shadow: 0 6px 24px rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.upload-btn svg {
  flex-shrink: 0;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Refresh Button */
.refresh-btn {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.refresh-btn:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
  transform: rotate(180deg);
}

/* Loading & Empty States */
.loading-container,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 32px;
  gap: 16px;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(99, 102, 241, 0.2);
  border-top-color: #6366F1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  color: var(--text-secondary);
  font-size: 14px;
}

.empty-state svg {
  color: var(--text-tertiary);
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 20px;
  color: var(--text-primary);
}

.empty-state p {
  color: var(--text-secondary);
  font-size: 14px;
}

/* Papers Grid - List View */
.papers-grid {
  display: flex !important;
  flex-direction: column !important;
  gap: 16px;
  width: 100%;
}

.paper-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  transition: all 0.3s ease;
}

.paper-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(102, 126, 234, 0.5);
  transform: translateY(-2px);
}

.paper-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: rgba(102, 126, 234, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-primary);
  flex-shrink: 0;
}

.paper-info {
  flex: 1;
  min-width: 0;
}

.paper-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.paper-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: var(--text-tertiary);
}

.paper-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid var(--border-primary);
  background: var(--bg-secondary);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
}

.download-btn:hover {
  border-color: var(--accent-success);
  color: var(--accent-success);
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
}

.delete-btn:hover {
  border-color: var(--accent-danger);
  color: var(--accent-danger);
  box-shadow: 0 0 20px rgba(255, 107, 157, 0.3);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-glow);
  border-radius: 16px;
  box-shadow: var(--shadow-lg);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--border-primary);
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: transparent;
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: rgba(255, 107, 157, 0.1);
  border-color: var(--accent-danger);
  color: var(--accent-danger);
}

.modal-body {
  padding: 24px;
}

.modal-body p {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 12px;
}

.paper-name-preview {
  color: var(--text-primary);
  font-weight: 500;
  background: rgba(102, 126, 234, 0.1);
  padding: 12px;
  border-radius: 8px;
  word-break: break-all;
}

.warning-text {
  color: var(--accent-danger);
  font-size: 13px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid var(--border-primary);
  justify-content: flex-end;
}

.btn-secondary,
.btn-danger {
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-danger {
  background: linear-gradient(135deg, #ff6b9d 0%, #c44569 100%);
  border: none;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(255, 107, 157, 0.5);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Animations */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  display: inline-block;
  width: 48px;
  height: 48px;
  border: 4px solid rgba(102, 126, 234, 0.2);
  border-radius: 50%;
  border-top-color: var(--accent-primary);
  animation: spin 0.8s linear infinite;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal-content {
  transform: scale(0.95);
}

.modal-leave-to .modal-content {
  transform: scale(0.95);
}

/* Search Results Info */
.search-results-info {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.results-header {
  flex: 1;
}

.results-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px 0;
  line-height: 1.4;
}

.results-count {
  font-size: 13px;
  color: var(--text-tertiary);
  font-weight: normal;
}

.search-time {
  font-size: 12px;
  color: var(--text-tertiary);
  font-family: 'Courier New', monospace;
}

.clear-results-btn {
  padding: 10px 20px;
  border-radius: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.clear-results-btn:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
  transform: translateY(-1px);
}

/* Search Results Grid */
.search-results-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Paper Result Card */
.paper-result-card {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  padding: 24px;
  transition: all 0.3s ease;
}

.paper-result-card:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
  transform: translateY(-2px);
}

/* Paper Header */
.paper-result-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-primary);
}

.paper-doc-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-primary);
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.paper-result-card:hover .paper-doc-icon {
  background: rgba(102, 126, 234, 0.1);
  border-color: var(--border-glow);
}

.paper-result-info {
  flex: 1;
  min-width: 0;
}

.paper-result-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 10px 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.paper-result-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-item svg {
  opacity: 0.6;
}

.meta-divider {
  opacity: 0.3;
}

.sections-count {
  font-weight: 500;
  color: var(--accent-primary);
}

/* Relevance Indicator */
.relevance-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px;
  border-radius: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  flex-shrink: 0;
  min-width: 80px;
}

.relevance-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.relevance-indicator.high .relevance-circle {
  background: rgba(0, 255, 136, 0.1);
  color: var(--accent-success);
}

.relevance-indicator.medium .relevance-circle {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

.relevance-indicator.low .relevance-circle {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
}

.relevance-text {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.relevance-indicator.high .relevance-text {
  color: var(--accent-success);
}

.relevance-indicator.medium .relevance-text {
  color: #ffc107;
}

.relevance-indicator.low .relevance-text {
  color: var(--text-tertiary);
}

/* Preview Section */
.paper-preview {
  margin-bottom: 20px;
}

.preview-header {
  margin-bottom: 12px;
}

.preview-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.preview-sections {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-section {
  padding: 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 10px;
  transition: all 0.3s ease;
}

.preview-section:hover {
  border-color: rgba(102, 126, 234, 0.3);
  background: rgba(102, 126, 234, 0.03);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-badge {
  font-size: 11px;
  font-weight: 500;
  color: var(--accent-primary);
  background: rgba(102, 126, 234, 0.1);
  padding: 4px 10px;
  border-radius: 12px;
}

.section-pages {
  font-size: 11px;
  color: var(--text-tertiary);
  font-family: 'Courier New', monospace;
}

.section-content {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0;
}

.more-sections {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 10px;
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: center;
  justify-content: center;
}

.more-sections svg {
  opacity: 0.5;
}

/* Result Actions */
.paper-result-actions {
  display: flex;
  gap: 8px;
  padding-top: 20px;
  border-top: 1px solid var(--border-primary);
}

.result-action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.result-action-btn:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
  transform: translateY(-1px);
}

.result-action-btn.btn-primary {
  background: var(--gradient-primary);
  border: none;
  color: white;
}

.result-action-btn.btn-primary:hover {
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
}

/* Responsive */
@media (max-width: 768px) {
  .library-header {
    flex-direction: column;
    gap: 20px;
  }

  .header-actions {
    width: 100%;
  }

  .search-container {
    max-width: 100%;
  }

  .search-input {
    font-size: 14px;
  }

  .search-hint {
    font-size: 11px;
  }

  .section-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
    padding-bottom: 16px;
  }

  .section-title-wrapper {
    width: 100%;
    justify-content: space-between;
  }

  .section-actions {
    width: 100%;
    gap: 8px;
  }

  .upload-btn {
    flex: 1;
    padding: 10px 16px;
    font-size: 13px;
    justify-content: center;
  }

  .refresh-btn {
    width: 44px;
    height: 44px;
    flex-shrink: 0;
  }

  .paper-card {
    flex-wrap: wrap;
  }

  .paper-info {
    flex: 1 1 100%;
    margin-bottom: 12px;
  }

  .paper-actions {
    margin-left: auto;
  }
  
  /* Search Results Responsive */
  .search-results-info {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
    padding: 16px 20px;
  }
  
  .clear-results-btn {
    width: 100%;
    justify-content: center;
  }
  
  .paper-result-header {
    flex-wrap: wrap;
  }
  
  .relevance-indicator {
    flex-direction: row;
    width: 100%;
    justify-content: center;
  }
  
  .paper-result-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
  
  .paper-result-actions {
    flex-direction: column;
  }
  
  .result-action-btn {
    width: 100%;
  }
}
</style>

