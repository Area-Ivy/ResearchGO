<template>
  <div class="paper-library">
    <!-- Header -->
    <div class="library-header">
      <div class="header-section">
        <h1 class="page-title">Paper Library</h1>
        <p class="page-subtitle">Manage your research papers</p>
      </div>
      <div class="header-actions">
        <div class="search-box">
          <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search papers..."
            class="search-input"
          />
        </div>
      </div>
    </div>

    <!-- Upload Section -->
    <div class="upload-section">
      <div 
        class="upload-dropzone"
        :class="{ 'dragover': isDragOver, 'uploading': isUploading }"
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".pdf"
          @change="handleFileSelect"
          style="display: none"
        />
        <div class="upload-icon">
          <svg v-if="!isUploading" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <div v-else class="spinner"></div>
        </div>
        <h3 v-if="!isUploading">{{ isDragOver ? 'Drop PDF file here' : 'Upload PDF File' }}</h3>
        <p v-if="!isUploading">Drag and drop or click to select</p>
        <p v-else>Uploading...</p>
      </div>
      <div v-if="uploadError" class="error-message">
        {{ uploadError }}
      </div>
      <div v-if="uploadSuccess" class="success-message">
        File uploaded successfully!
      </div>
    </div>

    <!-- Papers List -->
    <div class="papers-section">
      <div class="section-header">
        <h2>Your Papers ({{ filteredPapers.length }})</h2>
        <button v-if="papers.length > 0" @click="loadPapers" class="refresh-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner"></div>
        <p class="loading-text">Loading papers...</p>
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
        <p>Try a different search term</p>
      </div>

      <div v-else class="papers-grid">
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

export default {
  name: 'PaperLibrary',
  data() {
    return {
      papers: [],
      searchQuery: '',
      isLoading: false,
      isUploading: false,
      isDeleting: false,
      isDragOver: false,
      uploadError: null,
      uploadSuccess: false,
      showDeleteModal: false,
      paperToDelete: null
    }
  },
  computed: {
    filteredPapers() {
      if (!this.searchQuery.trim()) {
        return this.papers
      }
      const query = this.searchQuery.toLowerCase()
      return this.papers.filter(paper =>
        paper.original_name.toLowerCase().includes(query)
      )
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
    handleDrop(event) {
      this.isDragOver = false
      const file = event.dataTransfer.files[0]
      if (file) {
        if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
          this.uploadFile(file)
        } else {
          this.uploadError = 'Only PDF files are allowed'
          setTimeout(() => {
            this.uploadError = null
          }, 3000)
        }
      }
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
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 10px 16px;
  min-width: 300px;
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
  font-size: 15px;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

/* Upload Section */
.upload-section {
  margin-bottom: 48px;
}

.upload-dropzone {
  background: rgba(255, 255, 255, 0.03);
  border: 2px dashed rgba(102, 126, 234, 0.3);
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-dropzone:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(102, 126, 234, 0.5);
}

.upload-dropzone.dragover {
  background: rgba(102, 126, 234, 0.1);
  border-color: var(--accent-primary);
  transform: scale(1.02);
}

.upload-dropzone.uploading {
  cursor: not-allowed;
  opacity: 0.7;
}

.upload-icon {
  margin-bottom: 16px;
  color: var(--accent-primary);
}

.upload-dropzone h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.upload-dropzone p {
  color: var(--text-secondary);
  font-size: 14px;
}

.error-message {
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(255, 107, 157, 0.1);
  border: 1px solid var(--accent-danger);
  border-radius: 8px;
  color: var(--accent-danger);
  font-size: 14px;
}

.success-message {
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid var(--accent-success);
  border-radius: 8px;
  color: var(--accent-success);
  font-size: 14px;
}

/* Papers Section */
.papers-section {
  margin-bottom: 48px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.refresh-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
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

/* Papers Grid */
.papers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.paper-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
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

/* Responsive */
@media (max-width: 768px) {
  .library-header {
    flex-direction: column;
  }

  .search-box {
    width: 100%;
    min-width: unset;
  }

  .upload-dropzone {
    padding: 32px 24px;
  }

  .papers-grid {
    grid-template-columns: 1fr;
  }

  .paper-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .paper-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>

