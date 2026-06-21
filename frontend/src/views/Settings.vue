<template>
  <div class="settings-page">
    <header class="settings-header">
      <div>
        <p class="eyebrow">Settings</p>
        <h1>System settings</h1>
        <p class="subtitle">Manage retrieval behavior, editable memory, and service health in one place.</p>
      </div>
      <button class="btn btn-secondary" type="button" :disabled="statusLoading" @click="loadSystemStatus">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="1 4 1 10 7 10"></polyline>
          <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
        </svg>
        <span>{{ statusLoading ? 'Refreshing' : 'Refresh status' }}</span>
      </button>
    </header>

    <section class="status-panel">
      <div class="section-heading">
        <div>
          <h2>Service status</h2>
          <p>{{ systemStatus.healthy }} of {{ systemStatus.total }} services healthy</p>
        </div>
        <span class="status-pill" :class="systemStatus.status">{{ systemStatus.status }}</span>
      </div>

      <div v-if="statusError" class="state state-error">{{ statusError }}</div>
      <div class="service-grid">
        <article v-for="service in services" :key="service.id" class="service-card">
          <div class="service-card-top">
            <h3>{{ service.name }}</h3>
            <span class="service-dot" :class="service.status"></span>
          </div>
          <p>{{ service.detail || service.status }}</p>
          <div class="service-meta">
            <span>{{ service.statusCode || 'N/A' }}</span>
            <span>{{ service.latencyMs }}ms</span>
          </div>
        </article>
      </div>
    </section>

    <section class="settings-grid">
      <article class="settings-panel">
        <div class="section-heading compact">
          <div>
            <h2>Retrieval settings</h2>
            <p>Control how paper retrieval ranks candidate chunks before answering.</p>
          </div>
          <span class="status-pill" :class="{ healthy: retrievalSettings.use_reranker, idle: !retrievalSettings.use_reranker }">
            {{ retrievalSettings.use_reranker ? 'Reranker on' : 'Reranker off' }}
          </span>
        </div>

        <div v-if="settingsError" class="state state-error">{{ settingsError }}</div>
        <div class="setting-list">
        <div class="setting-row">
          <div>
            <h3>Use reranker</h3>
            <p>{{ rerankerDescription }}</p>
          </div>
          <label class="switch">
            <input
              v-model="retrievalSettings.use_reranker"
              type="checkbox"
              :disabled="settingsLoading || settingsSaving"
              @change="saveRetrievalSettings"
            >
            <span class="switch-track">
              <span class="switch-thumb"></span>
            </span>
          </label>
        </div>
        <div class="setting-row">
          <div>
            <h3>Final chunks</h3>
            <p>How many ranked chunks are used as answer context.</p>
          </div>
          <div class="number-control">
            <input
              v-model.number="retrievalSettings.top_k"
              type="number"
              min="1"
              max="20"
              step="1"
              :disabled="settingsLoading || settingsSaving"
              @change="saveRetrievalSettings"
            >
          </div>
        </div>
        <div class="setting-row">
          <div>
            <h3>Candidate chunks</h3>
            <p>How many chunks each retrieval path collects before RRF and reranking.</p>
          </div>
          <div class="number-control">
            <input
              v-model.number="retrievalSettings.initial_k"
              type="number"
              min="5"
              max="100"
              step="5"
              :disabled="settingsLoading || settingsSaving"
              @change="saveRetrievalSettings"
            >
          </div>
        </div>
        </div>
      </article>

      <article class="memory-panel">
        <header class="memory-header">
          <div>
            <h2>Memory</h2>
            <div class="file-meta">
              <span>{{ fileName }}</span>
              <span v-if="updatedAt">Updated {{ formatDate(updatedAt) }}</span>
            </div>
          </div>
          <div class="actions">
            <button class="btn btn-secondary" type="button" :disabled="memoryLoading || memorySaving" @click="loadMemory">
              Revert
            </button>
            <button class="btn btn-primary" type="button" :disabled="memoryLoading || memorySaving" @click="saveMemory">
              {{ memorySaving ? 'Saving' : 'Save' }}
            </button>
          </div>
        </header>

        <div v-if="memoryError" class="state state-error">{{ memoryError }}</div>
        <div v-else-if="memoryNotice" class="state state-success">{{ memoryNotice }}</div>

        <div class="editor-panel">
          <div v-if="memoryLoading" class="loading-state">
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
        </div>

        <footer class="memory-footer">
          <div class="doc-stats">
            <span>{{ lineCount }} lines</span>
            <span>{{ byteCount }} bytes</span>
          </div>
          <button class="btn btn-danger" type="button" :disabled="memoryLoading || memorySaving" @click="clearMemory">
            Clear
          </button>
        </footer>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { clearMemoryDocument, getMemoryDocument, saveMemoryDocument } from '../api/memory'
import { getRetrievalSettings, updateRetrievalSettings } from '../api/retrievalSettings'
import { getSystemStatus } from '../api/system'

defineOptions({ name: 'Settings' })

const systemStatus = ref({
  status: 'idle',
  healthy: 0,
  total: 0,
  services: [],
  updatedAt: null
})
const statusLoading = ref(false)
const statusError = ref('')

const settingsLoading = ref(false)
const settingsSaving = ref(false)
const settingsError = ref('')
const retrievalSettings = ref({
  use_reranker: true,
  translate_query: true,
  top_k: 10,
  initial_k: 20
})

const content = ref('')
const fileName = ref('memory.md')
const updatedAt = ref(null)
const memoryLoading = ref(false)
const memorySaving = ref(false)
const memoryError = ref('')
const memoryNotice = ref('')

const services = computed(() => systemStatus.value.services || [])
const lineCount = computed(() => (content.value ? content.value.split('\n').length : 0))
const byteCount = computed(() => new Blob([content.value]).size)
const rerankerDescription = computed(() => (
  retrievalSettings.value.use_reranker
    ? 'Hybrid retrieval uses the cross-encoder reranker for higher precision.'
    : 'Hybrid retrieval skips reranking for faster responses with lower ranking precision.'
))

const setDocument = (document) => {
  content.value = document.content || ''
  fileName.value = document.file_name || 'memory.md'
  updatedAt.value = document.updated_at || null
}

const formatDate = (value) => {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

const loadSystemStatus = async () => {
  statusLoading.value = true
  statusError.value = ''
  try {
    systemStatus.value = await getSystemStatus()
  } catch (err) {
    statusError.value = err.response?.data?.detail || 'Failed to load system status.'
  } finally {
    statusLoading.value = false
  }
}

const loadRetrievalSettings = async () => {
  settingsLoading.value = true
  settingsError.value = ''
  try {
    retrievalSettings.value = {
      ...retrievalSettings.value,
      ...(await getRetrievalSettings())
    }
  } catch (err) {
    settingsError.value = err.response?.data?.detail || 'Failed to load retrieval settings.'
  } finally {
    settingsLoading.value = false
  }
}

const saveRetrievalSettings = async () => {
  settingsSaving.value = true
  settingsError.value = ''
  try {
    const topK = clampNumber(retrievalSettings.value.top_k, 1, 20)
    const initialK = clampNumber(retrievalSettings.value.initial_k, 5, 100)
    retrievalSettings.value.top_k = topK
    retrievalSettings.value.initial_k = Math.max(initialK, topK)
    retrievalSettings.value = {
      ...retrievalSettings.value,
      ...(await updateRetrievalSettings({
        use_reranker: retrievalSettings.value.use_reranker,
        top_k: retrievalSettings.value.top_k,
        initial_k: retrievalSettings.value.initial_k
      }))
    }
  } catch (err) {
    settingsError.value = err.response?.data?.detail || 'Failed to save retrieval settings.'
    await loadRetrievalSettings()
  } finally {
    settingsSaving.value = false
  }
}

const clampNumber = (value, min, max) => {
  const parsed = Number.parseInt(value, 10)
  if (Number.isNaN(parsed)) return min
  return Math.max(min, Math.min(max, parsed))
}

const loadMemory = async () => {
  memoryLoading.value = true
  memoryError.value = ''
  memoryNotice.value = ''
  try {
    setDocument(await getMemoryDocument())
  } catch (err) {
    memoryError.value = err.response?.data?.detail || 'Failed to load memory.'
  } finally {
    memoryLoading.value = false
  }
}

const saveMemory = async () => {
  memorySaving.value = true
  memoryError.value = ''
  memoryNotice.value = ''
  try {
    setDocument(await saveMemoryDocument(content.value))
    memoryNotice.value = 'Saved.'
  } catch (err) {
    memoryError.value = err.response?.data?.detail || 'Failed to save memory.'
  } finally {
    memorySaving.value = false
  }
}

const clearMemory = async () => {
  if (!window.confirm('Clear memory?')) return
  memorySaving.value = true
  memoryError.value = ''
  memoryNotice.value = ''
  try {
    setDocument(await clearMemoryDocument())
    memoryNotice.value = 'Cleared.'
  } catch (err) {
    memoryError.value = err.response?.data?.detail || 'Failed to clear memory.'
  } finally {
    memorySaving.value = false
  }
}

onMounted(() => {
  loadSystemStatus()
  loadRetrievalSettings()
  loadMemory()
})
</script>

<style scoped>
.settings-page {
  min-height: calc(100vh - 68px);
  display: flex;
  flex-direction: column;
  gap: 18px;
  color: var(--text-primary);
}

.settings-header,
.section-heading,
.memory-header,
.memory-footer,
.actions,
.doc-stats,
.service-card-top,
.service-meta {
  display: flex;
  align-items: center;
  gap: 14px;
}

.settings-header {
  justify-content: space-between;
  align-items: flex-start;
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--accent-primary);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin: 0;
}

.settings-header h1 {
  color: var(--text-primary);
  font-size: 34px;
  font-weight: 850;
  line-height: 1.1;
}

h2 {
  font-size: 22px;
}

h3 {
  font-size: 15px;
}

.subtitle,
.section-heading p,
.setting-row p,
.service-card p,
.file-meta,
.doc-stats {
  color: var(--text-secondary);
}

.subtitle {
  margin-top: 8px;
  font-size: 15px;
}

.status-panel,
.settings-panel,
.memory-panel,
.service-card {
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  background:
    radial-gradient(circle at 90% 0%, rgba(56, 189, 248, 0.08), transparent 30%),
    rgba(15, 23, 42, 0.72);
  box-shadow: 0 20px 54px rgba(0, 0, 0, 0.18);
}

.status-panel,
.settings-panel,
.memory-panel {
  padding: 20px;
}

.section-heading {
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 18px;
}

.section-heading.compact {
  margin-bottom: 14px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.12);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

.status-pill.healthy {
  background: rgba(34, 197, 94, 0.14);
  color: #86efac;
}

.status-pill.degraded,
.status-pill.idle {
  background: rgba(250, 204, 21, 0.14);
  color: #fde68a;
}

.service-grid {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(170px, 1fr);
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.service-grid::-webkit-scrollbar {
  height: 6px;
}

.service-grid::-webkit-scrollbar-track {
  background: transparent;
}

.service-grid::-webkit-scrollbar-thumb {
  background: rgba(56, 189, 248, 0.62);
  border-radius: 999px;
}

.service-card {
  min-width: 170px;
  padding: 14px;
}

.service-card-top,
.service-meta {
  justify-content: space-between;
}

.service-card p {
  min-height: 20px;
  margin-top: 8px;
  font-size: 13px;
}

.service-meta {
  margin-top: 14px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.service-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #94a3b8;
  box-shadow: 0 0 18px rgba(148, 163, 184, 0.36);
}

.service-dot.healthy {
  background: #22c55e;
  box-shadow: 0 0 18px rgba(34, 197, 94, 0.46);
}

.service-dot.degraded {
  background: #facc15;
  box-shadow: 0 0 18px rgba(250, 204, 21, 0.46);
}

.service-dot.down {
  background: #f43f5e;
  box-shadow: 0 0 18px rgba(244, 63, 94, 0.46);
}

.settings-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.8fr) minmax(480px, 1.2fr);
  gap: 18px;
  align-items: stretch;
}

.setting-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 16px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 8px;
  background: rgba(5, 8, 23, 0.42);
}

.number-control {
  flex: 0 0 auto;
}

.number-control input[type="number"] {
  width: 76px;
  height: 36px;
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  background: rgba(5, 8, 23, 0.54);
  color: var(--text-primary);
  font-weight: 800;
  text-align: center;
  outline: none;
}

.number-control input[type="number"]:focus {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
}

.switch {
  position: relative;
  width: 54px;
  height: 30px;
  flex: 0 0 auto;
}

.switch input {
  position: absolute;
  opacity: 0;
}

.switch-track {
  position: absolute;
  inset: 0;
  cursor: pointer;
  border-radius: 999px;
  background: rgba(71, 85, 105, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.22);
  transition: all 0.2s ease;
}

.switch-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ffffff;
  transition: transform 0.2s ease;
}

.switch input:checked + .switch-track {
  background: var(--gradient-primary);
  border-color: transparent;
}

.switch input:checked + .switch-track .switch-thumb {
  transform: translateX(24px);
}

.memory-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.memory-header,
.memory-footer {
  justify-content: space-between;
  align-items: flex-start;
}

.file-meta,
.doc-stats {
  margin-top: 6px;
  font-size: 13px;
}

.editor-panel {
  flex: 1;
  min-height: 0;
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  overflow: hidden;
  background: rgba(5, 8, 23, 0.48);
}

.memory-editor {
  width: 100%;
  min-height: 0;
  height: 100%;
  max-height: 100%;
  padding: 20px;
  resize: none;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 14px;
  line-height: 1.7;
}

.loading-state {
  min-height: 220px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(56, 189, 248, 0.25);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
  background: rgba(15, 23, 42, 0.76);
  cursor: pointer;
  font-weight: 700;
}

.btn:disabled {
  opacity: 0.58;
  cursor: not-allowed;
}

.btn-primary {
  border-color: transparent;
  background: var(--gradient-primary);
  color: #fff;
}

.btn-secondary:hover {
  border-color: var(--border-glow);
  color: var(--accent-primary);
}

.btn-danger {
  border-color: rgba(244, 63, 94, 0.28);
  color: #fda4af;
}

.state {
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 13px;
}

.state-error {
  border: 1px solid rgba(244, 63, 94, 0.35);
  background: rgba(127, 29, 29, 0.18);
  color: #fda4af;
}

.state-success {
  border: 1px solid rgba(34, 197, 94, 0.32);
  background: rgba(20, 83, 45, 0.16);
  color: #86efac;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1100px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .settings-header,
  .memory-header,
  .memory-footer,
  .setting-row {
    flex-direction: column;
    align-items: stretch;
  }

  .settings-header h1 {
    font-size: 28px;
  }

  .actions {
    width: 100%;
  }

  .number-control {
    width: 100%;
    min-width: 0;
  }

  .btn {
    flex: 1;
  }
}
</style>
