<template>
  <div class="memory-page">
    <header class="memory-header">
      <div class="title-block">
        <h1>Memory</h1>
        <div class="file-meta">
          <span>{{ fileName }}</span>
          <span v-if="updatedAt">Updated {{ formatDate(updatedAt) }}</span>
        </div>
      </div>
      <div class="actions">
        <button class="btn btn-secondary" type="button" :disabled="loading || saving" @click="loadMemory">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="1 4 1 10 7 10"></polyline>
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
          </svg>
          <span>Revert</span>
        </button>
        <button class="btn btn-primary" type="button" :disabled="loading || saving" @click="saveMemory">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
            <polyline points="17 21 17 13 7 13 7 21"></polyline>
            <polyline points="7 3 7 8 15 8"></polyline>
          </svg>
          <span>{{ saving ? 'Saving' : 'Save' }}</span>
        </button>
      </div>
    </header>

    <div v-if="error" class="state state-error">{{ error }}</div>
    <div v-else-if="notice" class="state state-success">{{ notice }}</div>

    <section class="editor-panel">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>Loading memory</span>
      </div>
      <textarea
        v-else
        v-model="content"
        class="memory-editor"
        spellcheck="false"
        aria-label="Memory markdown"
      ></textarea>
    </section>

    <footer class="memory-footer">
      <div class="doc-stats">
        <span>{{ lineCount }} lines</span>
        <span>{{ byteCount }} bytes</span>
      </div>
      <button class="btn btn-danger" type="button" :disabled="loading || saving" @click="clearMemory">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path>
          <path d="M10 11v6"></path>
          <path d="M14 11v6"></path>
          <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"></path>
        </svg>
        <span>Clear</span>
      </button>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { clearMemoryDocument, getMemoryDocument, saveMemoryDocument } from '../api/memory'

const content = ref('')
const fileName = ref('memory.md')
const updatedAt = ref(null)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const notice = ref('')

const lineCount = computed(() => content.value ? content.value.split('\n').length : 0)
const byteCount = computed(() => new Blob([content.value]).size)

const setDocument = (document) => {
  content.value = document.content || ''
  fileName.value = document.file_name || 'memory.md'
  updatedAt.value = document.updated_at || null
}

const formatDate = (value) => {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

const loadMemory = async () => {
  loading.value = true
  error.value = ''
  notice.value = ''
  try {
    setDocument(await getMemoryDocument())
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load memory.'
  } finally {
    loading.value = false
  }
}

const saveMemory = async () => {
  saving.value = true
  error.value = ''
  notice.value = ''
  try {
    setDocument(await saveMemoryDocument(content.value))
    notice.value = 'Saved.'
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save memory.'
  } finally {
    saving.value = false
  }
}

const clearMemory = async () => {
  if (!window.confirm('Clear memory?')) return

  saving.value = true
  error.value = ''
  notice.value = ''
  try {
    setDocument(await clearMemoryDocument())
    notice.value = 'Cleared.'
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to clear memory.'
  } finally {
    saving.value = false
  }
}

onMounted(loadMemory)
</script>

<style scoped>
.memory-page {
  min-height: calc(100vh - 68px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: var(--text-primary);
}

.memory-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.title-block h1 {
  margin: 0 0 8px;
  font-size: 30px;
  line-height: 1.1;
  font-weight: 800;
  color: var(--text-primary);
}

.file-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.actions,
.memory-footer,
.doc-stats {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid var(--border-primary);
  font-weight: 700;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, color 0.2s ease;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--gradient-primary);
  color: #fff;
  border-color: transparent;
}

.btn-secondary {
  background: rgba(15, 23, 42, 0.78);
  color: var(--text-secondary);
}

.btn-secondary:hover:not(:disabled) {
  color: var(--accent-primary);
  border-color: var(--border-glow);
}

.btn-danger {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.32);
  color: #fca5a5;
}

.state {
  border-radius: 8px;
  padding: 12px 14px;
  border: 1px solid;
  font-size: 14px;
}

.state-error {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.35);
  color: #fecaca;
}

.state-success {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.32);
  color: #bbf7d0;
}

.editor-panel {
  position: relative;
  flex: 1;
  min-height: 520px;
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  background: rgba(8, 13, 28, 0.78);
  overflow: hidden;
  box-shadow: 0 18px 46px rgba(0, 0, 0, 0.22);
}

.memory-editor {
  width: 100%;
  height: 100%;
  min-height: 520px;
  padding: 22px;
  resize: vertical;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font: 14px/1.65 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  tab-size: 2;
}

.memory-editor::selection {
  background: rgba(56, 189, 248, 0.26);
}

.loading-state {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.spinner {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid rgba(148, 163, 184, 0.35);
  border-top-color: var(--accent-primary);
  animation: spin 0.9s linear infinite;
}

.memory-footer {
  justify-content: space-between;
  color: var(--text-tertiary);
  font-size: 13px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .memory-page {
    min-height: calc(100vh - 64px);
  }

  .memory-header,
  .memory-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .actions {
    width: 100%;
  }

  .btn {
    flex: 1;
  }

  .editor-panel,
  .memory-editor {
    min-height: 480px;
  }
}
</style>
