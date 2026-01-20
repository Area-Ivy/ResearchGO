<template>
  <div class="milvus-manager">
    <!-- Header -->
    <div class="manager-header">
      <div class="header-section">
        <h1 class="page-title">
          <svg class="title-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
            <polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline>
            <polyline points="7.5 19.79 7.5 14.6 3 12"></polyline>
            <polyline points="21 12 16.5 14.6 16.5 19.79"></polyline>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
            <line x1="12" y1="22.08" x2="12" y2="12"></line>
          </svg>
          Milvus Vector Database
        </h1>
        <p class="page-subtitle">Manage collections and vector data</p>
      </div>
      <div class="header-status">
        <div class="status-indicator" :class="{ connected: isConnected }">
          <span class="status-dot"></span>
          <span class="status-text">{{ isConnected ? 'Connected' : 'Disconnected' }}</span>
        </div>
        <button @click="checkConnection" class="refresh-btn" title="Refresh Connection">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- Stats Overview -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-icon collections-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ collections.length }}</div>
          <div class="stat-label">Collections</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon vectors-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ formatNumber(totalVectors) }}</div>
          <div class="stat-label">Total Vectors</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon memory-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ loadedCollections }}</div>
          <div class="stat-label">Loaded</div>
        </div>
      </div>
    </div>

    <!-- Collections Section -->
    <div class="collections-section">
      <div class="section-header">
        <h2>Collections</h2>
        <div class="header-actions">
          <div class="search-box">
            <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search collections..."
              class="search-input"
            />
          </div>
          <button @click="showCreateModal = true" class="btn-primary">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Create Collection
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner"></div>
        <p class="loading-text">Loading collections...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="collections.length === 0" class="empty-state">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
        <h3>No Collections Yet</h3>
        <p>Create your first collection to get started</p>
        <button @click="showCreateModal = true" class="btn-primary">Create Collection</button>
      </div>

      <!-- Collections Grid -->
      <div v-else class="collections-grid">
        <div
          v-for="collection in filteredCollections"
          :key="collection.name"
          class="collection-card"
          :class="{ loaded: collection.loaded }"
        >
          <div class="collection-header">
            <div class="collection-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <div class="collection-info">
              <h3 class="collection-name">{{ collection.name }}</h3>
              <p class="collection-description">{{ collection.description || 'No description' }}</p>
            </div>
            <div v-if="collection.loaded" class="loaded-badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              Loaded
            </div>
          </div>
          
          <div class="collection-stats">
            <div class="stat-item">
              <span class="stat-label">Vectors</span>
              <span class="stat-value">{{ formatNumber(collection.num_entities) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Dimension</span>
              <span class="stat-value">{{ collection.dimension || '-' }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Index</span>
              <span class="stat-value">{{ collection.index_type || 'None' }}</span>
            </div>
          </div>

          <div class="collection-actions">
            <button 
              @click="toggleLoad(collection)" 
              class="action-btn"
              :class="{ active: collection.loaded }"
              :title="collection.loaded ? 'Release' : 'Load'"
            >
              <svg v-if="!collection.loaded" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
              </svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="1 4 1 10 7 10"></polyline>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
              </svg>
              {{ collection.loaded ? 'Release' : 'Load' }}
            </button>
            <button @click="viewCollection(collection)" class="action-btn view-btn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              View
            </button>
            <button @click="confirmDelete(collection)" class="action-btn delete-btn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Collection Modal -->
    <transition name="modal">
      <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>Create New Collection</h3>
            <button @click="showCreateModal = false" class="modal-close">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Collection Name</label>
              <input
                v-model="newCollection.name"
                type="text"
                placeholder="e.g., research_papers"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label>Description</label>
              <textarea
                v-model="newCollection.description"
                placeholder="Optional description..."
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>
            <div class="form-group">
              <label>Vector Dimension</label>
              <input
                v-model.number="newCollection.dimension"
                type="number"
                placeholder="e.g., 768 for BERT, 1536 for OpenAI"
                class="form-input"
              />
              <span class="form-hint">Common: 384 (MiniLM), 768 (BERT), 1536 (OpenAI)</span>
            </div>
            <div v-if="createError" class="error-message">
              {{ createError }}
            </div>
          </div>
          <div class="modal-actions">
            <button @click="showCreateModal = false" class="btn-secondary">Cancel</button>
            <button @click="createCollection" class="btn-primary" :disabled="isCreating || !newCollection.name || !newCollection.dimension">
              {{ isCreating ? 'Creating...' : 'Create Collection' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Delete Confirmation Modal -->
    <transition name="modal">
      <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>Delete Collection</h3>
            <button @click="showDeleteModal = false" class="modal-close">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete this collection?</p>
            <p class="collection-name-preview">{{ collectionToDelete?.name }}</p>
            <p class="warning-text">⚠️ This will delete all {{ formatNumber(collectionToDelete?.num_entities) }} vectors in this collection. This action cannot be undone.</p>
          </div>
          <div class="modal-actions">
            <button @click="showDeleteModal = false" class="btn-secondary">Cancel</button>
            <button @click="deleteCollection" class="btn-danger" :disabled="isDeleting">
              {{ isDeleting ? 'Deleting...' : 'Delete Collection' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Collection Detail Modal -->
    <transition name="modal">
      <div v-if="showDetailModal" class="modal-overlay" @click="showDetailModal = false">
        <div class="modal-content modal-large" @click.stop>
          <div class="modal-header">
            <h3>{{ selectedCollection?.name }}</h3>
            <button @click="showDetailModal = false" class="modal-close">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="detail-section">
              <h4>Collection Info</h4>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">Name</span>
                  <span class="info-value">{{ selectedCollection?.name }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Description</span>
                  <span class="info-value">{{ selectedCollection?.description || '-' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Vector Count</span>
                  <span class="info-value">{{ formatNumber(selectedCollection?.num_entities) }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Dimension</span>
                  <span class="info-value">{{ selectedCollection?.dimension }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Index Type</span>
                  <span class="info-value">{{ selectedCollection?.index_type || 'None' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Status</span>
                  <span class="info-value">
                    <span class="status-badge" :class="{ loaded: selectedCollection?.loaded }">
                      {{ selectedCollection?.loaded ? 'Loaded' : 'Not Loaded' }}
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'MilvusManager',
  data() {
    return {
      collections: [],
      searchQuery: '',
      isLoading: false,
      isCreating: false,
      isDeleting: false,
      isConnected: false,
      showCreateModal: false,
      showDeleteModal: false,
      showDetailModal: false,
      collectionToDelete: null,
      selectedCollection: null,
      createError: null,
      newCollection: {
        name: '',
        description: '',
        dimension: 768
      }
    }
  },
  computed: {
    filteredCollections() {
      if (!this.searchQuery.trim()) {
        return this.collections
      }
      const query = this.searchQuery.toLowerCase()
      return this.collections.filter(collection =>
        collection.name.toLowerCase().includes(query) ||
        (collection.description && collection.description.toLowerCase().includes(query))
      )
    },
    totalVectors() {
      return this.collections.reduce((sum, col) => sum + (col.num_entities || 0), 0)
    },
    loadedCollections() {
      return this.collections.filter(col => col.loaded).length
    }
  },
  mounted() {
    this.checkConnection()
    this.loadCollections()
  },
  methods: {
    async checkConnection() {
      try {
        const response = await fetch('http://localhost:8000/api/milvus/status')
        const data = await response.json()
        this.isConnected = data.connected
      } catch (error) {
        console.error('Failed to check connection:', error)
        this.isConnected = false
      }
    },
    async loadCollections() {
      this.isLoading = true
      try {
        const response = await fetch('http://localhost:8000/api/milvus/collections')
        const data = await response.json()
        this.collections = data.collections || []
      } catch (error) {
        console.error('Failed to load collections:', error)
      } finally {
        this.isLoading = false
      }
    },
    async createCollection() {
      if (!this.newCollection.name || !this.newCollection.dimension) {
        this.createError = 'Please fill in all required fields'
        return
      }

      this.isCreating = true
      this.createError = null

      try {
        const response = await fetch('http://localhost:8000/api/milvus/collections', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.newCollection)
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Failed to create collection')
        }

        this.showCreateModal = false
        this.newCollection = { name: '', description: '', dimension: 768 }
        await this.loadCollections()
      } catch (error) {
        console.error('Failed to create collection:', error)
        this.createError = error.message
      } finally {
        this.isCreating = false
      }
    },
    confirmDelete(collection) {
      this.collectionToDelete = collection
      this.showDeleteModal = true
    },
    async deleteCollection() {
      if (!this.collectionToDelete) return

      this.isDeleting = true
      try {
        const response = await fetch(`http://localhost:8000/api/milvus/collections/${this.collectionToDelete.name}`, {
          method: 'DELETE'
        })

        if (!response.ok) {
          throw new Error('Failed to delete collection')
        }

        this.showDeleteModal = false
        this.collectionToDelete = null
        await this.loadCollections()
      } catch (error) {
        console.error('Failed to delete collection:', error)
        alert('Failed to delete collection: ' + error.message)
      } finally {
        this.isDeleting = false
      }
    },
    async toggleLoad(collection) {
      try {
        const action = collection.loaded ? 'release' : 'load'
        const response = await fetch(`http://localhost:8000/api/milvus/collections/${collection.name}/${action}`, {
          method: 'POST'
        })

        if (!response.ok) {
          throw new Error(`Failed to ${action} collection`)
        }

        await this.loadCollections()
      } catch (error) {
        console.error('Failed to toggle load:', error)
        alert(error.message)
      }
    },
    viewCollection(collection) {
      this.selectedCollection = collection
      this.showDetailModal = true
    },
    formatNumber(num) {
      if (!num) return '0'
      if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M'
      }
      if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K'
      }
      return num.toString()
    }
  }
}
</script>

<style scoped>
.milvus-manager {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
  padding: 2rem;
  color: #e0e7ff;
}

/* Header */
.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 2rem;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.title-icon {
  stroke: #60a5fa;
  filter: drop-shadow(0 0 10px rgba(96, 165, 250, 0.5));
}

.page-subtitle {
  color: #94a3b8;
  font-size: 1rem;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 2rem;
  backdrop-filter: blur(10px);
}

.status-indicator.connected {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.1);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  animation: pulse 2s infinite;
}

.status-indicator.connected .status-dot {
  background: #22c55e;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 0.875rem;
  font-weight: 500;
}

/* Stats Section */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: rgba(96, 165, 250, 0.3);
  box-shadow: 0 10px 30px rgba(96, 165, 250, 0.2);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.collections-icon {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
}

.vectors-icon {
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
}

.memory-icon {
  background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
}

.stat-icon svg {
  stroke: white;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #e0e7ff;
}

.stat-label {
  color: #94a3b8;
  font-size: 0.875rem;
}

/* Section Header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #e0e7ff;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 1rem;
  stroke: #64748b;
  pointer-events: none;
}

.search-input {
  padding: 0.75rem 1rem 0.75rem 3rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  color: #e0e7ff;
  font-size: 0.875rem;
  width: 250px;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: rgba(96, 165, 250, 0.5);
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1);
}

.search-input::placeholder {
  color: #64748b;
}

/* Buttons */
.btn-primary, .btn-secondary, .btn-danger {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(96, 165, 250, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #e0e7ff;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.btn-danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(239, 68, 68, 0.4);
}

.refresh-btn {
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(96, 165, 250, 0.3);
}

.refresh-btn svg {
  stroke: #94a3b8;
}

/* Loading & Empty States */
.loading-container {
  text-align: center;
  padding: 4rem 2rem;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(96, 165, 250, 0.2);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: #94a3b8;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: rgba(255, 255, 255, 0.02);
  border: 2px dashed rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
}

.empty-state svg {
  stroke: #475569;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.25rem;
  color: #e0e7ff;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #94a3b8;
  margin-bottom: 1.5rem;
}

/* Collections Grid */
.collections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.collection-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 1.5rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.collection-card:hover {
  transform: translateY(-4px);
  border-color: rgba(96, 165, 250, 0.3);
  box-shadow: 0 10px 30px rgba(96, 165, 250, 0.2);
}

.collection-card.loaded {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.05);
}

.collection-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.collection-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.collection-icon svg {
  stroke: white;
}

.collection-info {
  flex: 1;
  min-width: 0;
}

.collection-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #e0e7ff;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.collection-description {
  font-size: 0.875rem;
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loaded-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 1rem;
  font-size: 0.75rem;
  color: #22c55e;
  font-weight: 500;
}

.loaded-badge svg {
  stroke: #22c55e;
}

.collection-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  padding: 1rem 0;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 1rem;
}

.stat-item {
  text-align: center;
}

.stat-item .stat-label {
  display: block;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 0.25rem;
}

.stat-item .stat-value {
  display: block;
  font-size: 1.125rem;
  font-weight: 600;
  color: #e0e7ff;
}

.collection-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-btn {
  flex: 1;
  min-width: fit-content;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  color: #e0e7ff;
  font-size: 0.875rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(96, 165, 250, 0.3);
}

.action-btn.active {
  background: rgba(34, 197, 94, 0.2);
  border-color: rgba(34, 197, 94, 0.3);
  color: #22c55e;
}

.action-btn.delete-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.action-btn svg {
  stroke: currentColor;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
}

.modal-content.modal-large {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #e0e7ff;
}

.modal-close {
  padding: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #94a3b8;
  transition: color 0.3s ease;
}

.modal-close:hover {
  color: #e0e7ff;
}

.modal-body {
  padding: 1.5rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  justify-content: flex-end;
}

.collection-name-preview {
  font-weight: 600;
  color: #60a5fa;
  margin: 1rem 0;
  padding: 0.75rem;
  background: rgba(96, 165, 250, 0.1);
  border-radius: 0.5rem;
  border: 1px solid rgba(96, 165, 250, 0.2);
}

.warning-text {
  color: #f59e0b;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Form Styles */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #e0e7ff;
  margin-bottom: 0.5rem;
}

.form-input, .form-textarea {
  width: 100%;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  color: #e0e7ff;
  font-size: 0.875rem;
  transition: all 0.3s ease;
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: rgba(96, 165, 250, 0.5);
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1);
}

.form-input::placeholder, .form-textarea::placeholder {
  color: #64748b;
}

.form-hint {
  display: block;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}

.error-message {
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.5rem;
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 1rem;
}

/* Detail Section */
.detail-section {
  margin-bottom: 2rem;
}

.detail-section h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #e0e7ff;
  margin-bottom: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.info-item {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
}

.info-label {
  display: block;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 0.25rem;
}

.info-value {
  display: block;
  font-size: 1rem;
  font-weight: 600;
  color: #e0e7ff;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 1rem;
  font-size: 0.75rem;
  color: #ef4444;
  font-weight: 500;
}

.status-badge.loaded {
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
}

/* Transitions */
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9);
}

/* Responsive */
@media (max-width: 768px) {
  .milvus-manager {
    padding: 1rem;
  }

  .page-title {
    font-size: 2rem;
  }

  .manager-header {
    flex-direction: column;
  }

  .collections-grid {
    grid-template-columns: 1fr;
  }

  .stats-section {
    grid-template-columns: 1fr;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  .search-input {
    width: 100%;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>

