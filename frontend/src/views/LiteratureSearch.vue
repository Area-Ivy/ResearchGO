<template>
  <div class="literature-search">
    <div class="search-header">
      <div class="header-section">
        <h1 class="page-title">Literature Search</h1>
        <p class="page-subtitle">Powered by OpenAlex - 250M+ Academic Papers</p>
      </div>
      <div class="header-actions">
        <!-- 预留操作按钮位置，暂时为空 -->
      </div>
    </div>

    <!-- Search Bar -->
    <div class="search-container">
      <div class="search-box">
        <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        <input
          v-model="searchQuery"
          @keyup.enter="handleSearch"
          type="text"
          placeholder="Search papers by title, author, keywords..."
          class="search-input"
        />
        <button
          v-if="searchQuery"
          @click="clearSearch"
          class="clear-button"
          type="button"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
        <button
          @click="handleSearch"
          class="search-button"
          :disabled="!searchQuery || isLoading"
          type="button"
        >
          <span v-if="!isLoading">Search</span>
          <span v-else>Searching...</span>
        </button>
      </div>
      
      <button @click="showFilters = !showFilters" class="filter-toggle" type="button">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
        </svg>
        <span>Filters</span>
        <span v-if="activeFiltersCount > 0" class="filter-count">{{ activeFiltersCount }}</span>
      </button>
    </div>

    <!-- Filters Panel -->
    <transition name="slide-down">
      <div v-if="showFilters" class="filters-panel">
        <div class="filter-group">
          <label class="filter-label">Publication Year</label>
          <div class="year-range">
            <input
              v-model.number="filters.publication_year_start"
              type="number"
              placeholder="From"
              class="year-input"
              min="1900"
              :max="currentYear"
            />
            <span class="range-separator">-</span>
            <input
              v-model.number="filters.publication_year_end"
              type="number"
              placeholder="To"
              class="year-input"
              min="1900"
              :max="currentYear"
            />
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">Citations</label>
          <div class="citation-range">
            <input
              v-model.number="filters.min_cited_by_count"
              type="number"
              placeholder="Min citations"
              class="citation-input"
              min="0"
            />
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-checkbox">
            <input v-model="filters.open_access_only" type="checkbox" />
            <span>Open Access Only</span>
          </label>
        </div>

        <div class="filter-actions">
          <button @click="applyFilters" class="btn-primary" type="button">Apply Filters</button>
          <button @click="clearFilters" class="btn-secondary" type="button">Clear</button>
        </div>
      </div>
    </transition>

    <!-- Sort and View Options -->
    <div v-if="hasSearched" class="results-toolbar">
      <div class="results-info">
        <span v-if="!isLoading">
          Found <strong>{{ totalResults.toLocaleString() }}</strong> results
        </span>
      </div>
      
      <div class="sort-options">
        <label class="sort-label">Sort by:</label>
        <select v-model="sortBy" @change="handleSort" class="sort-select">
          <option value="relevance">Relevance</option>
          <option value="cited_by_count">Citations</option>
          <option value="publication_date">Publication Date</option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">Searching OpenAlex database...</p>
    </div>

    <!-- Error State -->
    <div v-if="error && !isLoading" class="error-container">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <h3>Search Error</h3>
      <p>{{ error }}</p>
      <button @click="handleSearch" class="btn-primary" type="button">Try Again</button>
    </div>

    <!-- Empty State -->
    <div v-if="!hasSearched && !isLoading && !error" class="empty-state">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
      </svg>
      <h3>Start Your Literature Search</h3>
      <p>Search 250+ million academic papers from OpenAlex</p>
      <div class="search-examples">
        <p class="examples-title">Try searching for:</p>
        <button @click="searchExample('machine learning')" class="example-chip" type="button">machine learning</button>
        <button @click="searchExample('climate change')" class="example-chip" type="button">climate change</button>
        <button @click="searchExample('quantum computing')" class="example-chip" type="button">quantum computing</button>
      </div>
    </div>

    <!-- Results List -->
    <div v-if="results.length > 0 && !isLoading" class="results-container">
      <div class="results-list">
        <div
          v-for="work in results"
          :key="work.id"
          class="work-card"
          @click="showWorkDetail(work)"
        >
          <div class="work-header">
            <h3 class="work-title">{{ work.title }}</h3>
            <div class="work-badges">
              <span v-if="work.open_access?.is_oa" class="badge badge-oa">Open Access</span>
              <span v-if="work.type" class="badge badge-type">{{ formatWorkType(work.type) }}</span>
            </div>
          </div>

          <div class="work-authors">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>{{ formatAuthors(work.authors) }}</span>
          </div>

          <div class="work-meta">
            <span v-if="work.publication_year" class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              {{ work.publication_year }}
            </span>
            
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
              </svg>
              {{ work.cited_by_count }} citations
            </span>

            <span v-if="work.venue" class="meta-item venue">
              {{ work.venue }}
            </span>
          </div>

          <div v-if="work.abstract" class="work-abstract">
            {{ truncateText(work.abstract, 200) }}
          </div>

          <div class="work-actions">
            <button @click.stop="showWorkDetail(work)" class="btn-action" type="button">
              View Details
            </button>
            <button @click.stop="discussWithAI(work)" class="btn-action" type="button">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
              Discuss with AI
            </button>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          @click="goToPage(currentPage - 1)"
          :disabled="currentPage === 1"
          class="pagination-button"
          type="button"
        >
          Previous
        </button>
        
        <div class="pagination-info">
          Page {{ currentPage }} of {{ totalPages }}
        </div>
        
        <button
          @click="goToPage(currentPage + 1)"
          :disabled="currentPage >= totalPages"
          class="pagination-button"
          type="button"
        >
          Next
        </button>
      </div>
    </div>

    <!-- No Results -->
    <div v-if="hasSearched && results.length === 0 && !isLoading && !error" class="no-results">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
      <h3>No Results Found</h3>
      <p>Try adjusting your search query or filters</p>
    </div>

    <!-- Work Detail Modal -->
    <transition name="modal">
      <div v-if="selectedWork" class="modal-overlay" @click="closeModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h2 class="modal-title">{{ selectedWork.title }}</h2>
            <button @click="closeModal" class="modal-close" type="button">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="work-detail-section">
              <h4>Authors</h4>
              <div class="authors-list">
                <span v-for="(author, index) in selectedWork.authors" :key="index" class="author-tag">
                  {{ author.name }}
                </span>
              </div>
            </div>

            <div class="work-detail-section" v-if="selectedWork.abstract">
              <h4>Abstract</h4>
              <p class="abstract-text">{{ selectedWork.abstract }}</p>
            </div>

            <div class="work-detail-section">
              <h4>Publication Information</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">Year:</span>
                  <span class="detail-value">{{ selectedWork.publication_year || 'N/A' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Citations:</span>
                  <span class="detail-value">{{ selectedWork.cited_by_count }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Venue:</span>
                  <span class="detail-value">{{ selectedWork.venue || 'N/A' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Type:</span>
                  <span class="detail-value">{{ formatWorkType(selectedWork.type) }}</span>
                </div>
              </div>
            </div>

            <div class="work-detail-section" v-if="selectedWork.doi">
              <h4>Links</h4>
              <div class="links-container">
                <a :href="selectedWork.doi_url" target="_blank" class="external-link">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                  </svg>
                  DOI: {{ selectedWork.doi }}
                </a>
                <a v-if="selectedWork.open_access?.oa_url" :href="selectedWork.open_access.oa_url" target="_blank" class="external-link">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                  Open Access PDF
                </a>
              </div>
            </div>

            <div class="modal-actions">
              <button @click="generateSummary" :disabled="isSummarizing" class="btn-primary" type="button">
                <span v-if="!isSummarizing">Generate AI Summary</span>
                <span v-else>Generating...</span>
              </button>
              <button @click="discussWithAI(selectedWork)" class="btn-primary" type="button">
                Discuss with AI
              </button>
              <button @click="showExportDialog" class="btn-secondary" type="button">
                Export Citation
              </button>
            </div>

            <!-- AI Summary Section -->
            <div v-if="aiSummary" class="work-detail-section summary-section">
              <h4>AI Summary</h4>
              <div class="summary-content">
                <div class="summary-item">
                  <h5>研究背景</h5>
                  <p>{{ aiSummary.background }}</p>
                </div>
                <div class="summary-item">
                  <h5>研究方法</h5>
                  <p>{{ aiSummary.method }}</p>
                </div>
                <div class="summary-item">
                  <h5>核心发现</h5>
                  <p>{{ aiSummary.findings }}</p>
                </div>
                <div class="summary-item">
                  <h5>研究意义</h5>
                  <p>{{ aiSummary.significance }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Export Dialog -->
    <transition name="modal">
      <div v-if="showExport" class="modal-overlay" @click="showExport = false">
        <div class="modal-content export-modal" @click.stop>
          <div class="modal-header">
            <h3>Export Citation</h3>
            <button @click="showExport = false" class="modal-close" type="button">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          
          <div class="modal-body">
            <div class="export-formats">
              <button
                v-for="format in ['bibtex', 'ris', 'apa', 'mla']"
                :key="format"
                @click="handleExport(format)"
                :class="['export-format-btn', { active: exportFormat === format }]"
                type="button"
              >
                {{ format.toUpperCase() }}
              </button>
            </div>

            <div v-if="exportContent" class="export-preview">
              <pre>{{ exportContent }}</pre>
              <button @click="copyToClipboard" class="btn-primary" type="button">
                {{ copied ? 'Copied!' : 'Copy to Clipboard' }}
              </button>
            </div>

            <div v-if="isExporting" class="loading-container">
              <div class="loading-spinner"></div>
              <p>Generating citation...</p>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'Literature'
}
</script>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { searchWorks, getWorkDetail, summarizeWork, exportCitations } from '../api/literature'

const router = useRouter()

// Search state
const searchQuery = ref('')
const hasSearched = ref(false)
const isLoading = ref(false)
const error = ref(null)

// Filters
const showFilters = ref(false)
const filters = ref({
  publication_year_start: null,
  publication_year_end: null,
  min_cited_by_count: null,
  open_access_only: false
})

const currentYear = new Date().getFullYear()

// Results
const results = ref([])
const totalResults = ref(0)
const currentPage = ref(1)
const perPage = ref(20)
const totalPages = ref(0)
const sortBy = ref('relevance')

// Detail modal
const selectedWork = ref(null)
const aiSummary = ref(null)
const isSummarizing = ref(false)

// Export
const showExport = ref(false)
const exportFormat = ref('bibtex')
const exportContent = ref('')
const isExporting = ref(false)
const copied = ref(false)

// Computed
const activeFiltersCount = computed(() => {
  let count = 0
  if (filters.value.publication_year_start) count++
  if (filters.value.publication_year_end) count++
  if (filters.value.min_cited_by_count) count++
  if (filters.value.open_access_only) count++
  return count
})

// Methods
async function handleSearch() {
  if (!searchQuery.value.trim()) return

  isLoading.value = true
  error.value = null
  hasSearched.value = true
  currentPage.value = 1

  try {
    const response = await searchWorks({
      query: searchQuery.value,
      filters: buildFilters(),
      page: currentPage.value,
      per_page: perPage.value,
      sort: sortBy.value
    })

    results.value = response.results
    totalResults.value = response.total
    totalPages.value = response.total_pages
  } catch (err) {
    error.value = err.message || 'Failed to search literature'
    results.value = []
  } finally {
    isLoading.value = false
  }
}

function buildFilters() {
  const activeFilters = {}
  if (filters.value.publication_year_start) {
    activeFilters.publication_year_start = filters.value.publication_year_start
  }
  if (filters.value.publication_year_end) {
    activeFilters.publication_year_end = filters.value.publication_year_end
  }
  if (filters.value.min_cited_by_count) {
    activeFilters.min_cited_by_count = filters.value.min_cited_by_count
  }
  if (filters.value.open_access_only) {
    activeFilters.open_access_only = true
  }
  return Object.keys(activeFilters).length > 0 ? activeFilters : null
}

function applyFilters() {
  showFilters.value = false
  handleSearch()
}

function clearFilters() {
  filters.value = {
    publication_year_start: null,
    publication_year_end: null,
    min_cited_by_count: null,
    open_access_only: false
  }
  handleSearch()
}

function clearSearch() {
  searchQuery.value = ''
  results.value = []
  hasSearched.value = false
  error.value = null
}

function handleSort() {
  handleSearch()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  handleSearch()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function searchExample(query) {
  searchQuery.value = query
  handleSearch()
}

function showWorkDetail(work) {
  selectedWork.value = work
  aiSummary.value = null
}

function closeModal() {
  selectedWork.value = null
  aiSummary.value = null
}

async function generateSummary() {
  if (!selectedWork.value || !selectedWork.value.id) return

  isSummarizing.value = true
  try {
    const workId = selectedWork.value.id.split('/').pop()
    const response = await summarizeWork(workId, 'zh')
    aiSummary.value = response.summary
  } catch (err) {
    alert('Failed to generate summary: ' + err.message)
  } finally {
    isSummarizing.value = false
  }
}

function discussWithAI(work) {
  // Navigate to chat with work context
  const workInfo = {
    title: work.title,
    authors: work.authors.map(a => a.name).join(', '),
    year: work.publication_year,
    abstract: work.abstract,
    citations: work.cited_by_count
  }
  
  router.push({
    name: 'Chat',
    query: {
      context: 'literature',
      workId: work.id,
      workTitle: work.title
    },
    state: { workInfo }
  })
}

function showExportDialog() {
  showExport.value = true
  exportContent.value = ''
  exportFormat.value = 'bibtex'
}

async function handleExport(format) {
  exportFormat.value = format
  isExporting.value = true
  exportContent.value = ''
  copied.value = false

  try {
    if (!selectedWork.value || !selectedWork.value.id) {
      alert('This work does not have a valid ID')
      isExporting.value = false
      return
    }
    const workId = selectedWork.value.id.split('/').pop()
    const response = await exportCitations([workId], format)
    exportContent.value = response.content
  } catch (err) {
    alert('Failed to export citation: ' + err.message)
  } finally {
    isExporting.value = false
  }
}

function copyToClipboard() {
  navigator.clipboard.writeText(exportContent.value)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

// Utility functions
function formatAuthors(authors) {
  if (!authors || authors.length === 0) return 'Unknown authors'
  if (authors.length === 1) return authors[0].name
  if (authors.length <= 3) return authors.map(a => a.name).join(', ')
  return `${authors[0].name} et al.`
}

function formatWorkType(type) {
  if (!type) return 'Article'
  return type.split('-').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

function truncateText(text, maxLength) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
.literature-search {
  max-width: 1600px;
  margin: 0 auto;
  min-height: 100vh;
}

.search-header {
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
  display: flex;
  gap: 12px;
  align-items: center;
}

/* Search Container */
.search-container {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  transition: all 0.3s ease;
}

.search-box:focus-within {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(102, 126, 234, 0.5);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-icon {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 1rem;
}

.search-input::placeholder {
  color: var(--text-secondary);
}

.clear-button {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.clear-button:hover {
  color: var(--text-primary);
}

.search-button {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  border: none;
  color: white;
  padding: 0.5rem 1.5rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.search-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.6);
}

.search-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 0.75rem 1.5rem;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.filter-toggle:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(102, 126, 234, 0.5);
}

.filter-count {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  color: white;
  padding: 0.125rem 0.5rem;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
}

/* Filters Panel */
.filters-panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
}

.year-range,
.citation-range {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.year-input,
.citation-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.5rem;
  color: var(--text-primary);
  font-size: 0.875rem;
}

.range-separator {
  color: var(--text-secondary);
}

.filter-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.filter-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.filter-actions {
  display: flex;
  gap: 0.75rem;
  grid-column: 1 / -1;
}

/* Results Toolbar */
.results-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
}

.results-info {
  color: var(--text-secondary);
}

.results-info strong {
  color: var(--text-primary);
}

.sort-options {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sort-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.sort-select {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  color: var(--text-primary);
  cursor: pointer;
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 1rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(99, 102, 241, 0.2);
  border-top-color: #6366F1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: var(--text-secondary);
}

/* Empty State */
.empty-state,
.error-container,
.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 1rem;
  text-align: center;
}

.empty-state svg,
.error-container svg,
.no-results svg {
  color: var(--text-secondary);
  opacity: 0.5;
}

.empty-state h3,
.error-container h3,
.no-results h3 {
  font-size: 1.5rem;
  color: var(--text-primary);
}

.empty-state p,
.error-container p,
.no-results p {
  color: var(--text-secondary);
  max-width: 500px;
}

.search-examples {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.examples-title {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.example-chip {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #6366F1;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.example-chip:hover {
  background: rgba(102, 126, 234, 0.2);
  transform: translateY(-2px);
}

/* Work Card */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.work-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.work-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(102, 126, 234, 0.5);
  transform: translateY(-2px);
}

.work-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.work-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  flex: 1;
}

.work-badges {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge-oa {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.badge-type {
  background: rgba(99, 102, 241, 0.1);
  color: #6366F1;
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.work-authors {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.work-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.meta-item.venue {
  color: var(--text-primary);
  font-style: italic;
}

.work-abstract {
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.work-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-action {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #6366F1;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-action:hover {
  background: rgba(102, 126, 234, 0.2);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 2rem 0;
}

.pagination-button {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  padding: 0.5rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination-button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(102, 126, 234, 0.5);
}

.pagination-button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.pagination-info {
  color: var(--text-secondary);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
  overflow-y: auto;
}

.modal-content {
  background: var(--card-bg);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  background: var(--card-bg);
  z-index: 10;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
  padding-right: 1rem;
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  flex-shrink: 0;
  transition: color 0.2s;
}

.modal-close:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
}

.work-detail-section {
  margin-bottom: 2rem;
}

.work-detail-section h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
}

.authors-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.author-tag {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #6366F1;
  padding: 0.375rem 0.75rem;
  border-radius: 16px;
  font-size: 0.875rem;
}

.abstract-text {
  color: var(--text-secondary);
  line-height: 1.8;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.detail-value {
  color: var(--text-primary);
  font-weight: 500;
}

.links-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.external-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6366F1;
  text-decoration: none;
  transition: color 0.2s;
}

.external-link:hover {
  color: #8B5CF6;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(99, 102, 241, 0.6);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.05);
}

/* Summary Section */
.summary-section {
  background: rgba(102, 126, 234, 0.05);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.summary-item h5 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6366F1;
  margin-bottom: 0.5rem;
}

.summary-item p {
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Export Modal */
.export-modal {
  max-width: 600px;
}

.export-formats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.export-format-btn {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
}

.export-format-btn:hover {
  background: rgba(255, 255, 255, 0.05);
}

.export-format-btn.active {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  color: white;
  border-color: transparent;
}

.export-preview {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
}

.export-preview pre {
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin-bottom: 1rem;
  max-height: 300px;
  overflow-y: auto;
}

/* Transitions */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
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

/* Responsive */
@media (max-width: 768px) {
  .literature-search {
    padding: 0;
  }

  .search-header {
    flex-direction: column;
  }

  .search-container {
    flex-direction: column;
  }

  .filters-panel {
    grid-template-columns: 1fr;
  }

  .filter-actions {
    flex-direction: column;
  }

  .results-toolbar {
    flex-direction: column;
    align-items: start;
    gap: 1rem;
  }

  .work-header {
    flex-direction: column;
  }

  .work-actions {
    flex-direction: column;
  }

  .modal-content {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }

  .modal-actions {
    flex-direction: column;
  }

  .export-formats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

