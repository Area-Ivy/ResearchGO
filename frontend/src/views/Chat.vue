<template>
  <div class="chat-page">
    <!-- History Sidebar -->
    <aside class="chat-sidebar" :class="{ 'sidebar-open': sidebarOpen }">
      <div class="sidebar-header">
        <h2 class="sidebar-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          对话历史
        </h2>
        <button class="sidebar-toggle" @click="sidebarOpen = !sidebarOpen">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
      </div>

      <button class="new-chat-btn" @click="createNewChat">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        <span>新对话</span>
      </button>

      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          :class="['conversation-item', { active: currentConversation?.id === conv.id }]"
          @click="switchConversation(conv.id)"
        >
          <div class="conv-content">
            <div class="conv-title">{{ conv.title }}</div>
            <div class="conv-meta">
              {{ conv.message_count || 0 }} 条消息 · {{ formatTime(conv.updated_at) }}
            </div>
          </div>
          <button class="conv-delete" @click.stop="deleteChat(conv.id)" title="删除对话">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>

        <div v-if="conversations.length === 0" class="empty-conversations">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <p>暂无对话历史</p>
        </div>
      </div>
    </aside>

    <!-- Sidebar Overlay for Mobile -->
    <div class="sidebar-overlay" :class="{ 'active': sidebarOpen }" @click="sidebarOpen = false"></div>

    <!-- Main Chat Area -->
    <div class="chat-container">
      <div class="chat-header">
        <button class="mobile-menu-btn" @click="sidebarOpen = true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <div class="header-section">
          <h1 class="page-title">
            {{ currentConversation?.title || 'AI Research Assistant' }}
          </h1>
          <p class="page-subtitle">Ask me anything about your research</p>
        </div>
        <div class="header-actions">
          <input
            ref="paperUploadInput"
            type="file"
            accept=".pdf"
            class="paper-upload-input"
            @change="handlePaperUpload"
          >
          <button
            class="header-action-btn"
            :disabled="isUploadingPaper"
            @click="triggerPaperUpload"
          >
            {{ isUploadingPaper ? 'Uploading...' : 'Upload Paper' }}
          </button>
          <button
            class="header-action-btn secondary"
            :disabled="paperLibraryLoading"
            @click="openPaperLibrary"
          >
            {{ paperLibraryLoading ? 'Loading...' : 'Select Paper' }}
          </button>
          <!-- 棰勭暀鎿嶄綔鎸夐挳浣嶇疆 -->
        </div>
      </div>

    <div
      v-if="paperUploadNotice"
      class="paper-upload-notice"
      :class="paperUploadNoticeType"
    >
      {{ paperUploadNotice }}
    </div>

    <div v-if="attachedPapers.length > 0" class="attached-papers-bar">
      <div class="attached-papers-label">Attached papers</div>
      <div class="attached-papers-list">
        <div v-for="paper in attachedPapers" :key="paper.paper_id" class="attached-paper-chip">
          <div class="attached-paper-meta">
            <span class="attached-paper-name">{{ paper.name }}</span>
            <span class="attached-paper-id">{{ paper.paper_id }}</span>
          </div>
          <button class="chip-remove-btn" @click="removeAttachedPaper(paper.paper_id)">Remove</button>
        </div>
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="ai-logo-stage" aria-hidden="true">
          <div class="logo-halo halo-1"></div>
          <div class="logo-halo halo-2"></div>
          <div class="logo-orbit orbit-a"><span></span></div>
          <div class="logo-orbit orbit-b"><span></span></div>
          <div class="logo-orbit orbit-c"><span></span></div>
          <div class="logo-particles">
            <span></span><span></span><span></span><span></span><span></span><span></span>
          </div>
          <div class="empty-icon">
            <svg width="78" height="78" viewBox="0 0 80 80" fill="none" aria-hidden="true">
              <circle class="core-ring" cx="40" cy="40" r="23" />
              <circle class="core-ring core-ring-inner" cx="40" cy="40" r="14" />
              <path class="core-arc" d="M28 47C31.6 53 38.8 56.2 46 54.6C53.2 53 58.6 46.7 59 39.4" />
              <path class="core-arc core-arc-secondary" d="M52 33C48.4 27 41.2 23.8 34 25.4C26.8 27 21.4 33.3 21 40.6" />
              <circle class="core-pulse" cx="40" cy="40" r="6.5" />
            </svg>
          </div>
          <div class="logo-reflection"></div>
        </div>
        <div class="empty-copy">
          <div class="empty-kicker">ResearchGO Neural Core</div>
          <h3>Start a Conversation</h3>
          <p>Ask me about research papers, concepts, or anything else you'd like to know.</p>
        </div>
      </div>

      <div v-for="(message, index) in messages" :key="index" class="message" :class="'message-' + message.role">
        <div class="message-avatar">
          <svg v-if="message.role === 'user'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7L12 12L22 7L12 2Z"></path>
            <path d="M2 17L12 22L22 17"></path>
            <path d="M2 12L12 17L22 12"></path>
          </svg>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-role">{{ message.role === 'user' ? 'You' : 'AI Assistant' }}</span>
            <span class="message-time">{{ message.time }}</span>
          </div>
          <div class="message-text" v-html="message.content"></div>
          <div v-if="message.mindmaps?.length" class="message-mindmaps">
            <div v-for="mindmap in message.mindmaps" :key="mindmap.id" class="mindmap-card">
              <div class="mindmap-card-header">
                <div class="mindmap-card-title">思维导图</div>
                <div class="mindmap-card-subtitle">{{ mindmap.title }}</div>
              </div>
              <div class="mindmap-card-body">
                <div :id="mindmap.id" class="chat-jsmind-container"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="isLoading" class="message message-assistant">
        <div class="message-avatar">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7L12 12L22 7L12 2Z"></path>
            <path d="M2 17L12 22L22 17"></path>
            <path d="M2 12L12 17L22 12"></path>
          </svg>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-role">AI Assistant</span>
          </div>
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-container">
      <div class="chat-input-wrapper">
        <div class="input-plus-menu">
          <button
            class="plus-btn"
            :disabled="isUploadingPaper || paperLibraryLoading"
            @click="showInputActions = !showInputActions"
          >
            +
          </button>
          <div v-if="showInputActions" class="input-actions-popover">
            <button class="input-action-item" @click="triggerPaperUploadAndClose">
              {{ isUploadingPaper ? 'Uploading...' : 'Upload Paper' }}
            </button>
            <button class="input-action-item" @click="openPaperLibraryFromInput">
              {{ paperLibraryLoading ? 'Loading...' : 'Select Paper' }}
            </button>
          </div>
        </div>
        <textarea 
          v-model="inputMessage" 
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.enter.shift.exact="inputMessage += '\n'"
          placeholder="Type your message... (Shift+Enter for new line)"
          class="chat-input"
          rows="1"
          ref="inputTextarea"
        ></textarea>
        <button 
          class="send-btn" 
          @click="sendMessage" 
          :disabled="!inputMessage.trim() || isLoading"
        >
          <svg v-if="!isLoading" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
          <span v-else class="spinner"></span>
        </button>
      </div>
    </div>

    </div>
  </div>

  <div
    v-if="paperLibraryOpen"
    class="paper-library-overlay"
    @click.self="paperLibraryOpen = false"
  >
    <div class="paper-library-modal">
      <div class="paper-library-header">
        <div>
          <h3>My Papers</h3>
          <p>Select a paper to attach to this conversation</p>
        </div>
        <button class="paper-library-close" @click="paperLibraryOpen = false">Close</button>
      </div>
      <div v-if="paperLibraryError" class="paper-library-error">{{ paperLibraryError }}</div>
      <div v-if="paperLibraryNotice" class="paper-library-notice">{{ paperLibraryNotice }}</div>
      <div v-if="paperLibraryLoading" class="paper-library-empty">Loading papers...</div>
      <div v-else-if="availablePapers.length === 0" class="paper-library-empty">
        No uploaded papers yet.
      </div>
      <div v-else class="paper-library-list">
        <button
          v-for="paper in availablePapers"
          :key="paper.object_name"
          class="paper-library-item"
          :class="{ disabled: !isPaperReady(paper) }"
          :disabled="!isPaperReady(paper)"
          @click="attachLibraryPaper(paper)"
        >
          <div class="paper-library-title">{{ paper.title || paper.original_name }}</div>
          <div class="paper-library-subtitle">{{ paper.original_name }}</div>
          <div class="paper-library-status-row">
            <span class="paper-library-status-badge" :class="paper.processing_status">
              {{ formatPaperProcessingStatus(paper.processing_status) }}
            </span>
            <span class="paper-library-status-text">{{ getPaperStatusDetail(paper) }}</span>
          </div>
          <div class="paper-library-id">{{ paper.object_name }}</div>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Chat'
}
</script>

<script setup>
import { ref, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import katex from 'katex'
import hljs from 'highlight.js'
import jsMind from 'jsmind'
import 'highlight.js/styles/atom-one-dark.css'
import 'katex/dist/katex.min.css'
import 'jsmind/style/jsmind.css'
import { API_ENDPOINTS } from '../config'
import {
  createConversation,
  getConversations,
  getConversation,
  addMessage,
  deleteConversation,
  updateConversation
} from '../api/conversations'
import { listPapers, uploadPaper } from '../api/papers'

const route = useRoute()

// Configure marked
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch (err) {
        console.error(err)
      }
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true
})

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputTextarea = ref(null)
const paperUploadInput = ref(null)
const error = ref(null)

const conversations = ref([])
const currentConversation = ref(null)
const sidebarOpen = ref(false)
const attachedPapers = ref([])
const availablePapers = ref([])
const paperLibraryOpen = ref(false)
const paperLibraryLoading = ref(false)
const paperLibraryError = ref('')
const paperLibraryNotice = ref('')
const isUploadingPaper = ref(false)
const showInputActions = ref(false)
const paperUploadNotice = ref('')
const paperUploadNoticeType = ref('info')
let paperLibraryPollTimer = null
const ATTACHED_PAPERS_STORAGE_KEY = 'researchgo_chat_attached_papers'
const chatMindmapInstances = new Map()

// Render LaTeX with KaTeX
const renderLatex = (text) => {
  if (!text) return text
  
  // Check if formula is likely to be valid LaTeX
  const isValidLatex = (formula) => {
    const trimmed = formula.trim()
    // Empty or too short
    if (!trimmed || trimmed.length < 2) return false
    // Only numbers or simple text (likely placeholder)
    if (/^[0-9\s]+$/.test(trimmed)) return false
    // Should contain LaTeX-like content
    return /[\\_{}\^=+\-*/()]|\\[a-zA-Z]+/.test(trimmed)
  }
  
  // Preprocess different LaTeX delimiters
  // Convert \[...\] to $$...$$
  text = text.replace(/\\\[([\s\S]*?)\\\]/g, (match, content) => {
    return isValidLatex(content) ? `$$${content}$$` : match
  })
  // Convert \(...\) to $...$
  text = text.replace(/\\\((.*?)\\\)/g, (match, content) => {
    return isValidLatex(content) ? `$${content}$` : match
  })
  // Convert [...] on its own line to $$...$$ only if it looks like LaTeX
  text = text.replace(/^\s*\[([\s\S]*?)\]\s*$/gm, (match, content) => {
    return isValidLatex(content) ? `$$${content}$$` : match
  })
  
  try {
    // First, render block math ($$...$$)
    text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
      const trimmed = formula.trim()
      if (!isValidLatex(trimmed)) {
        return match // Keep original if not valid LaTeX
      }
      try {
        const html = katex.renderToString(trimmed, {
          displayMode: true,
          throwOnError: false,
          trust: true,
          strict: false
        })
        // Check if KaTeX actually rendered something meaningful
        if (html && !html.includes('katex-error')) {
          return `<div class="katex-block">${html}</div>`
        }
        return match
      } catch (err) {
        console.warn('KaTeX block error:', err.message)
        return match
      }
    })
    
    // Then, render inline math ($...$)
    text = text.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
      const trimmed = formula.trim()
      if (!isValidLatex(trimmed)) {
        return match // Keep original if not valid LaTeX
      }
      try {
        const html = katex.renderToString(trimmed, {
          displayMode: false,
          throwOnError: false,
          trust: true,
          strict: false
        })
        // Check if KaTeX actually rendered something meaningful
        if (html && !html.includes('katex-error')) {
          return html
        }
        return match
      } catch (err) {
        console.warn('KaTeX inline error:', err.message)
        return match
      }
    })
  } catch (err) {
    console.error('LaTeX rendering error:', err)
  }
  
  return text
}

// 娓叉煋璁烘枃鍗＄墖
const renderPapersCards = (papersData) => {
  const { query, total, papers } = papersData
  
  if (!papers || papers.length === 0) {
    return `<div class="papers-empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
      </svg>
      <p>未找到相关论文</p>
    </div>`
  }
  
  // 鏍煎紡鍖栧紩鐢ㄦ暟
  const formatCitations = (num) => {
    if (num >= 10000) return (num / 1000).toFixed(1) + 'K'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num
  }
  
  let html = `<div class="papers-container">`
  html += `<div class="papers-header">
    <div class="papers-header-left">
      <div class="papers-icon-wrapper">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
        </svg>
      </div>
      <div class="papers-header-text">
        <span class="papers-count">${total || papers.length}</span>
        <span class="papers-label">篇相关论文</span>
      </div>
    </div>
    <div class="papers-query-badge">
      <span class="query-indicator"></span>
      <span>${query}</span>
    </div>
  </div>`
  
  html += `<div class="papers-grid">`
  
  for (let i = 0; i < Math.min(papers.length, 6); i++) {
    const paper = papers[i]
    const authors = paper.authors ? paper.authors.slice(0, 2).join(', ') + (paper.authors.length > 2 ? ' et al.' : '') : 'Unknown'
    const year = paper.year || 'N/A'
    const citations = paper.cited_by_count || 0
    const isOpenAccess = paper.open_access
    const abstract = paper.abstract ? paper.abstract.substring(0, 120) + '...' : ''
    const doi = paper.doi || ''
    
    let hotLevel = ''
    if (citations > 1000) hotLevel = 'hot-fire'
    else if (citations > 100) hotLevel = 'hot-warm'
    
    html += `
      <div class="paper-card ${hotLevel}" style="animation-delay: ${i * 0.05}s">
        <div class="paper-card-glow"></div>
        <div class="paper-card-inner">
          <div class="paper-card-header">
            <div class="paper-badges">
              ${isOpenAccess ? '<span class="paper-badge paper-badge-oa"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg> Open</span>' : ''}
              ${hotLevel === 'hot-fire' ? '<span class="paper-badge paper-badge-hot">馃敟 High Impact</span>' : ''}
            </div>
            <span class="paper-year-badge">${year}</span>
          </div>
          <h4 class="paper-title">${paper.title || 'Untitled'}</h4>
          <p class="paper-authors">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            ${authors}
          </p>
          ${abstract ? `<p class="paper-abstract">${abstract}</p>` : ''}
          <div class="paper-footer">
            <div class="paper-stats">
              <div class="stat-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 3v18h18"></path>
                  <path d="m19 9-5 5-4-4-3 3"></path>
                </svg>
                <span class="stat-value">${formatCitations(citations)}</span>
                <span class="stat-label">寮曠敤</span>
              </div>
            </div>
            ${doi ? `<a href="${doi}" target="_blank" class="paper-link">
              <span>鏌ョ湅璇︽儏</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                <polyline points="15 3 21 3 21 9"></polyline>
                <line x1="10" y1="14" x2="21" y2="3"></line>
              </svg>
            </a>` : ''}
          </div>
        </div>
      </div>
    `
  }
  
  html += `</div>`
  
  // 濡傛灉璁烘枃鏁伴噺瓒呰繃6绡囷紝鏄剧ず鏌ョ湅鏇村鎻愮ず
  if (papers.length > 6) {
    html += `<div class="papers-more">
      <span>杩樻湁 ${papers.length - 6} 绡囪鏂囨湭鏄剧ず</span>
    </div>`
  }
  
  html += `</div>`
  return html
}
const escapeHtml = (value) => String(value ?? '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')

const buildAssistantMessageContent = (message) => {
  return `${message.textHtml || ''}${message.artifactsHtml || ''}`
}

const syncAssistantMessageContent = (index) => {
  if (index === -1 || !messages.value[index]) return
  messages.value[index].content = buildAssistantMessageContent(messages.value[index])
}

const ensureAssistantMessage = () => {
  let assistantMessageIndex = messages.value.length - 1
  const lastMessage = messages.value[assistantMessageIndex]
  if (lastMessage?.role === 'assistant') {
    return assistantMessageIndex
  }

  assistantMessageIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    rawContent: '',
    textHtml: '',
    artifactsHtml: '',
    mindmaps: [],
    time: getCurrentTime()
  })
  return assistantMessageIndex
}

const appendAssistantArtifact = (index, html) => {
  if (index === -1 || !messages.value[index]) return
  messages.value[index].artifactsHtml = (messages.value[index].artifactsHtml || '') + html
  syncAssistantMessageContent(index)
}

const appendAssistantMindmap = async (index, mindmapPayload) => {
  if (index === -1 || !messages.value[index]) return

  const mindmapData = mindmapPayload?.mindmap_data
  if (!mindmapData) return

  const paperId = mindmapPayload?.paper_id || 'unknown-paper'
  const existing = (messages.value[index].mindmaps || []).find(item => item.paperId === paperId)
  if (existing) {
    await renderChatMindmap(existing.id, mindmapData)
    return
  }

  const mindmapId = `chat-mindmap-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  const title = mindmapData?.data?.topic || '论文思维导图'
  const nextMindmaps = [
    ...(messages.value[index].mindmaps || []),
    { id: mindmapId, paperId, title, data: mindmapData }
  ]
  messages.value[index].mindmaps = nextMindmaps
  await nextTick()
  await renderChatMindmap(mindmapId, mindmapData)
}

const addChatMindmapDragAndZoom = (container) => {
  if (!container || container.dataset.dragZoomBound === 'true') return

  let scale = 1
  const jsmindInner = container.querySelector('.jsmind-inner')
  if (!jsmindInner) return

  container.dataset.dragZoomBound = 'true'
  jsmindInner.style.transformOrigin = '0 0'
  jsmindInner.style.transition = 'transform 0.2s ease-out'

  container.addEventListener('wheel', (e) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault()
      const rect = container.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top
      const scrollLeft = container.scrollLeft
      const scrollTop = container.scrollTop
      const contentX = (mouseX + scrollLeft) / scale
      const contentY = (mouseY + scrollTop) / scale
      const delta = e.deltaY > 0 ? 0.9 : 1.1
      scale = Math.min(Math.max(scale * delta, 0.5), 2)
      jsmindInner.style.transform = `scale(${scale})`
      container.scrollLeft = contentX * scale - mouseX
      container.scrollTop = contentY * scale - mouseY
    }
  }, { passive: false })

  container.addEventListener('dblclick', (e) => {
    if (e.target === container || e.target.classList.contains('jsmind-inner')) {
      const centerX = (container.scrollLeft + container.clientWidth / 2) / scale
      const centerY = (container.scrollTop + container.clientHeight / 2) / scale
      scale = 1
      jsmindInner.style.transition = 'transform 0.3s ease'
      jsmindInner.style.transform = 'scale(1)'
      setTimeout(() => {
        container.scrollLeft = centerX - container.clientWidth / 2
        container.scrollTop = centerY - container.clientHeight / 2
        setTimeout(() => {
          jsmindInner.style.transition = 'transform 0.2s ease-out'
        }, 50)
      }, 50)
    }
  })
}

const renderChatMindmap = async (mindmapId, data) => {
  await nextTick()
  const container = document.getElementById(mindmapId)
  if (!container || !data) return

  container.innerHTML = ''
  chatMindmapInstances.delete(mindmapId)

  const instance = new jsMind({
    container,
    theme: 'primary',
    editable: false,
    view: {
      engine: 'canvas',
      hmargin: 100,
      vmargin: 50,
      line_width: 2,
      line_color: '#555'
    }
  })

  instance.show(data)
  addChatMindmapDragAndZoom(container)
  chatMindmapInstances.set(mindmapId, instance)
}

const normalizeAttachedPaper = (paper) => ({
  paper_id: paper.paper_id || paper.object_name || paper.id,
  name: paper.name || paper.title || paper.original_name || paper.paper_id || paper.object_name || 'Untitled paper'
})

const getAttachedPapersMap = () => {
  try {
    return JSON.parse(localStorage.getItem(ATTACHED_PAPERS_STORAGE_KEY) || '{}')
  } catch (err) {
    console.error('Failed to parse attached papers cache:', err)
    return {}
  }
}

const saveAttachedPapersForConversation = (conversationId, papers) => {
  if (!conversationId) return
  const paperMap = getAttachedPapersMap()
  paperMap[String(conversationId)] = papers
  localStorage.setItem(ATTACHED_PAPERS_STORAGE_KEY, JSON.stringify(paperMap))
}

const loadAttachedPapersForConversation = (conversationId) => {
  if (!conversationId) {
    attachedPapers.value = []
    return
  }
  const paperMap = getAttachedPapersMap()
  attachedPapers.value = (paperMap[String(conversationId)] || []).map(normalizeAttachedPaper)
}

const removeAttachedPapersForConversation = (conversationId) => {
  if (!conversationId) return
  const paperMap = getAttachedPapersMap()
  delete paperMap[String(conversationId)]
  localStorage.setItem(ATTACHED_PAPERS_STORAGE_KEY, JSON.stringify(paperMap))
}

const ensureConversationContext = async () => {
  if (currentConversation.value?.id) {
    return currentConversation.value
  }

  const conv = await createConversation('新对话')
  currentConversation.value = conv
  loadAttachedPapersForConversation(conv.id)
  await loadConversations()
  return conv
}

const persistAttachedPapers = () => {
  if (currentConversation.value?.id) {
    saveAttachedPapersForConversation(currentConversation.value.id, attachedPapers.value)
  }
}

const attachPaperToConversation = async (paper) => {
  const conversation = await ensureConversationContext()
  const normalizedPaper = normalizeAttachedPaper(paper)

  if (!normalizedPaper.paper_id) {
    throw new Error('Missing paper id from upload response')
  }

  const exists = attachedPapers.value.some(item => item.paper_id === normalizedPaper.paper_id)
  if (!exists) {
    attachedPapers.value = [...attachedPapers.value, normalizedPaper]
    saveAttachedPapersForConversation(conversation.id, attachedPapers.value)
  }
}

const triggerPaperUpload = () => {
  paperUploadInput.value?.click()
}

const triggerPaperUploadAndClose = () => {
  showInputActions.value = false
  triggerPaperUpload()
}

const setPaperUploadNotice = (message, type = 'info') => {
  paperUploadNotice.value = message
  paperUploadNoticeType.value = type
  window.setTimeout(() => {
    if (paperUploadNotice.value === message) {
      paperUploadNotice.value = ''
    }
  }, 5000)
}

const isPaperReady = (paper) => paper?.processing_status === 'indexed'

const formatPaperProcessingStatus = (status) => {
  if (status === 'indexed') return 'Indexed'
  if (status === 'indexing') return 'Indexing'
  if (status === 'failed') return 'Failed'
  return 'Uploaded'
}

const getPaperStatusDetail = (paper) => {
  if (paper?.processing_status === 'indexed') {
    return `${paper.chunks_created || 0} chunks ready`
  }
  if (paper?.processing_status === 'failed') {
    return paper.processing_error || 'Indexing failed'
  }
  if (paper?.processing_status === 'indexing') {
    return 'Still parsing and indexing'
  }
  return 'Waiting for indexing'
}

const stopPaperLibraryPolling = () => {
  if (paperLibraryPollTimer) {
    window.clearInterval(paperLibraryPollTimer)
    paperLibraryPollTimer = null
  }
}

const syncPaperLibraryPolling = () => {
  const hasIndexing = availablePapers.value.some(paper => paper.processing_status === 'indexing')
  if (!paperLibraryOpen.value || !hasIndexing) {
    stopPaperLibraryPolling()
    return
  }

  if (!paperLibraryPollTimer) {
    paperLibraryPollTimer = window.setInterval(async () => {
      if (!paperLibraryOpen.value || paperLibraryLoading.value) return
      try {
        const data = await listPapers()
        availablePapers.value = data.papers || []
        if (!availablePapers.value.some(paper => paper.processing_status === 'indexing')) {
          stopPaperLibraryPolling()
        }
      } catch (error) {
        console.error('Failed to poll paper library:', error)
      }
    }, 4000)
  }
}

const loadPaperLibrary = async () => {
  paperLibraryLoading.value = true
  paperLibraryError.value = ''
  try {
    const data = await listPapers()
    availablePapers.value = data.papers || []
    syncPaperLibraryPolling()
  } catch (err) {
    console.error('Failed to load paper library:', err)
    paperLibraryError.value = 'Failed to load your paper library.'
  } finally {
    paperLibraryLoading.value = false
  }
}

const openPaperLibrary = async () => {
  paperLibraryOpen.value = true
  paperLibraryNotice.value = ''
  await loadPaperLibrary()
}

const openPaperLibraryFromInput = async () => {
  showInputActions.value = false
  await openPaperLibrary()
}

const attachLibraryPaper = async (paper) => {
  if (!isPaperReady(paper)) {
    paperLibraryNotice.value = 'This paper is not ready yet. Please wait until indexing completes.'
    return
  }
  await attachPaperToConversation(paper)
  paperLibraryOpen.value = false
  showInputActions.value = false
  setPaperUploadNotice('Paper attached to this conversation.', 'success')
}

const handlePaperUpload = async (event) => {
  const [file] = Array.from(event.target?.files || [])
  if (!file) return

  isUploadingPaper.value = true
  paperLibraryError.value = ''
  paperLibraryNotice.value = ''

  try {
    const uploadedPaper = await uploadPaper(file)
    await loadPaperLibrary()
    const refreshedPaper = availablePapers.value.find(
      paper => paper.object_name === uploadedPaper.object_name
    )

    if (refreshedPaper && isPaperReady(refreshedPaper)) {
      await attachPaperToConversation(refreshedPaper)
      setPaperUploadNotice('Paper uploaded, indexed, and attached successfully.', 'success')
    } else {
      setPaperUploadNotice(
        uploadedPaper.message || 'Paper uploaded successfully. Indexing is still in progress.',
        uploadedPaper.processing_status === 'failed' ? 'error' : 'warning'
      )
    }
  } catch (err) {
    console.error('Failed to upload paper:', err)
    paperLibraryError.value = err.message || 'Failed to upload paper.'
    setPaperUploadNotice(paperLibraryError.value, 'error')
  } finally {
    isUploadingPaper.value = false
    if (event.target) {
      event.target.value = ''
    }
  }
}

const removeAttachedPaper = (paperId) => {
  attachedPapers.value = attachedPapers.value.filter(paper => paper.paper_id !== paperId)
  persistAttachedPapers()
}

// ============================================
// 瀵硅瘽绠＄悊鍑芥暟
// ============================================

// 鍔犺浇瀵硅瘽鍒楄〃
const loadConversations = async () => {
  try {
    const data = await getConversations(0, 50)
    conversations.value = data.conversations
  } catch (err) {
    console.error('鍔犺浇瀵硅瘽鍒楄〃澶辫触:', err)
  }
}

const createNewChat = async () => {
  try {
    // 濡傛灉姝ｅ湪鐢熸垚鍐呭锛屽厛淇濆瓨褰撳墠瀵硅瘽鐨勬渶鍚庝竴鏉I娑堟伅
    if (isLoading.value && currentConversation.value && messages.value.length > 0) {
      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage.role === 'assistant' && lastMessage.content) {
        const plainContent = lastMessage.content.replace(/<[^>]*>/g, '')
        if (plainContent.trim()) {
          await saveMessage('assistant', plainContent)
        }
      }
      isLoading.value = false
    }
    
    const conv = await createConversation('新对话')
    currentConversation.value = conv
    messages.value = []
    attachedPapers.value = []
    saveAttachedPapersForConversation(conv.id, [])
    await loadConversations()
    
    // 绉诲姩绔叧闂晶杈规爮
    if (window.innerWidth <= 1024) {
      sidebarOpen.value = false
    }
  } catch (err) {
    console.error('鍒涘缓瀵硅瘽澶辫触:', err)
    // 鍗充娇澶辫触涔熷厑璁哥户缁亰澶╋紙涓嶄繚瀛樺埌鏁版嵁搴擄級
    currentConversation.value = null
    messages.value = []
  }
}

// 鍒囨崲瀵硅瘽
const switchConversation = async (conversationId) => {
  try {
    // 濡傛灉姝ｅ湪鐢熸垚鍐呭锛屽厛淇濆瓨褰撳墠瀵硅瘽鐨勬渶鍚庝竴鏉I娑堟伅
    if (isLoading.value && currentConversation.value && messages.value.length > 0) {
      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage.role === 'assistant' && lastMessage.content) {
        const plainContent = lastMessage.content.replace(/<[^>]*>/g, '')
        if (plainContent.trim()) {
          await saveMessage('assistant', plainContent)
        }
      }
      isLoading.value = false
    }
    
    const conv = await getConversation(conversationId)
    currentConversation.value = conv
    loadAttachedPapersForConversation(conv.id)
    
    // 杞崲娑堟伅鏍煎紡
    messages.value = conv.messages.map(msg => ({
      role: msg.role,
      content: msg.role === 'user' ? msg.content : marked(renderLatex(msg.content)),
      time: formatMessageTime(msg.created_at)
    }))
    
    await nextTick()
    scrollToBottom()
    
    // 绉诲姩绔叧闂晶杈规爮
    if (window.innerWidth <= 1024) {
      sidebarOpen.value = false
    }
  } catch (err) {
    console.error('鍔犺浇瀵硅瘽澶辫触:', err)
  }
}

// 鍒犻櫎瀵硅瘽
const deleteChat = async (conversationId) => {
  if (!confirm('确定要删除这个对话吗？')) return
  
  try {
    await deleteConversation(conversationId)
    removeAttachedPapersForConversation(conversationId)
    
    if (currentConversation.value?.id === conversationId) {
      currentConversation.value = null
      messages.value = []
      attachedPapers.value = []
    }
    
    await loadConversations()
  } catch (err) {
    console.error('鍒犻櫎瀵硅瘽澶辫触:', err)
  }
}

// 淇濆瓨娑堟伅鍒版暟鎹簱
const saveMessage = async (role, content) => {
  if (!currentConversation.value) return
  
  try {
    await addMessage(currentConversation.value.id, role, content)
  } catch (err) {
    console.error('淇濆瓨娑堟伅澶辫触:', err)
  }
}

// 鏇存柊瀵硅瘽鏍囬锛堜娇鐢ㄧ涓€鏉℃秷鎭級
const updateConversationTitle = async (firstMessage) => {
  if (!currentConversation.value || currentConversation.value.title !== '新对话') return
  
  try {
    const title = firstMessage.substring(0, 30) + (firstMessage.length > 30 ? '...' : '')
    await updateConversation(currentConversation.value.id, title)
    currentConversation.value.title = title
    await loadConversations()
  } catch (err) {
    console.error('鏇存柊鏍囬澶辫触:', err)
  }
}

const formatTime = (dateString) => {
  if (!dateString) return ''
  
  // 瑙ｆ瀽鏃堕棿锛屽鏋滃悗绔繑鍥炵殑鏄?UTC 鏃堕棿瀛楃涓诧紙濡?"2024-01-20T10:30:00"锛?  // 闇€瑕佹坊鍔?'Z' 鎴栨槑纭寚瀹氫负 UTC
  let date = new Date(dateString)
  
  // 濡傛灉鏃堕棿瀛楃涓叉病鏈夋椂鍖轰俊鎭紝灏濊瘯娣诲姞鏃跺尯
  if (typeof dateString === 'string' && !dateString.includes('Z') && !dateString.includes('+')) {
    date = new Date(dateString.replace(' ', 'T'))
  }
  
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

const formatMessageTime = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userInput = inputMessage.value
  
  // 濡傛灉娌℃湁褰撳墠瀵硅瘽锛屽垱寤轰竴涓柊瀵硅瘽
  if (!currentConversation.value) {
    try {
      currentConversation.value = await createConversation('新对话')
      await loadConversations()
    } catch (err) {
      console.error('鍒涘缓瀵硅瘽澶辫触:', err)
      // 鍗充娇鍒涘缓澶辫触涔熺户缁紙涓嶄繚瀛樺埌鏁版嵁搴擄級
    }
  }

  const userMessage = {
    role: 'user',
    content: userInput,
    time: getCurrentTime()
  }

  messages.value.push(userMessage)
  inputMessage.value = ''

  // 娉ㄦ剰锛氱敤鎴锋秷鎭凡鍦?Agent Service 涓嚜鍔ㄤ繚瀛橈紝鏃犻渶鍓嶇鍐嶆淇濆瓨
  // 鏍囬涔熷湪 Agent Service 涓嚜鍔ㄧ敓鎴?
  // Auto-resize textarea
  if (inputTextarea.value) {
    inputTextarea.value.style.height = 'auto'
  }

  // Scroll to bottom
  await nextTick()
  scrollToBottom()

  // Call real API
  isLoading.value = true
  error.value = null
  
  try {
    // Build conversation history for context
    const conversationHistory = messages.value
      .filter(m => m.role !== 'system')
      .slice(-10) // Keep last 10 messages for context
      .map(m => ({
        role: m.role,
        content: typeof m.content === 'string' ? m.content.replace(/<[^>]*>/g, '') : m.content
      }))

    await nextTick()
    scrollToBottom()

    // Call Agent API with SSE
    const token = localStorage.getItem('token')
    const response = await fetch(API_ENDPOINTS.AGENT_CHAT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({
        message: userInput,
        conversation_id: currentConversation.value?.id,
        stream: true,
        attached_papers: attachedPapers.value
      })
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }

    // Read SSE stream from Agent Service
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullResponse = ''
    let assistantMessageIndex = -1
    let currentEvent = ''

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        // 瑙ｆ瀽浜嬩欢绫诲瀷
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim()
          continue
        }
        
        if (line.startsWith('data:')) {
          const data = line.slice(5).trim()
          
          if (!data || data === '') continue

          try {
            if (currentEvent === 'conversation') {
              const convData = JSON.parse(data)
              if (convData.conversation_id && !currentConversation.value) {
                currentConversation.value = { id: convData.conversation_id }
                console.log('New conversation created:', convData.conversation_id)
                await loadConversations()
              }
            } else if (currentEvent === 'thinking') {
              console.log('Agent thinking:', data)
              if (assistantMessageIndex === -1) {
                isLoading.value = false
                assistantMessageIndex = ensureAssistantMessage()
              }
              appendAssistantArtifact(
                assistantMessageIndex,
                `<div class="agent-thinking">${escapeHtml(JSON.parse(data))}</div>`
              )
              await nextTick()
              scrollToBottom()
            } else if (currentEvent === 'tool_call') {
              const toolData = JSON.parse(data)
              console.log('Tool call:', toolData)
              if (assistantMessageIndex !== -1) {
                appendAssistantArtifact(
                  assistantMessageIndex,
                  `<div class="agent-tool-call">Calling tool: ${escapeHtml(toolData.name)}</div>`
                )
                await nextTick()
                scrollToBottom()
              }
            } else if (currentEvent === 'papers') {
              const papersData = JSON.parse(data)
              console.log('Papers result:', papersData)
              if (assistantMessageIndex !== -1) {
                appendAssistantArtifact(assistantMessageIndex, renderPapersCards(papersData))
                await nextTick()
                scrollToBottom()
              }
            } else if (currentEvent === 'mindmap') {
              const mindmapData = JSON.parse(data)
              console.log('Mindmap result:', mindmapData)
              if (assistantMessageIndex !== -1) {
                await appendAssistantMindmap(assistantMessageIndex, mindmapData)
                scrollToBottom()
              }
            } else if (currentEvent === 'token') {
              const tokenContent = JSON.parse(data)
              if (assistantMessageIndex === -1) {
                isLoading.value = false
                assistantMessageIndex = ensureAssistantMessage()
              }
              messages.value[assistantMessageIndex].rawContent =
                (messages.value[assistantMessageIndex].rawContent || '') + tokenContent
              fullResponse = messages.value[assistantMessageIndex].rawContent
              messages.value[assistantMessageIndex].textHtml = marked(renderLatex(fullResponse))
              syncAssistantMessageContent(assistantMessageIndex)
              await nextTick()
              scrollToBottom()
            } else if (currentEvent === 'answer' || currentEvent === 'answer_end') {
              if (currentEvent === 'answer') {
                fullResponse = JSON.parse(data)
              }
              if (assistantMessageIndex === -1) {
                isLoading.value = false
                assistantMessageIndex = ensureAssistantMessage()
              }
              if (fullResponse) {
                messages.value[assistantMessageIndex].textHtml = marked(renderLatex(fullResponse))
                syncAssistantMessageContent(assistantMessageIndex)
              }
              await nextTick()
              scrollToBottom()
            } else if (currentEvent === 'error') {
              const errorData = JSON.parse(data)
              throw new Error(errorData.error || 'Agent error')
            } else if (currentEvent === 'done') {
              console.log('Agent done')
            }
          } catch (e) {
            if (e instanceof SyntaxError) {
              if (currentEvent === 'answer' && data) {
                fullResponse = data
                if (assistantMessageIndex === -1) {
                  isLoading.value = false
                  assistantMessageIndex = ensureAssistantMessage()
                }
                messages.value[assistantMessageIndex].textHtml = marked(renderLatex(fullResponse))
                syncAssistantMessageContent(assistantMessageIndex)
                await nextTick()
                scrollToBottom()
              }
              continue
            }
            throw e
          }
          }
        }
      }

    // 鍒锋柊瀵硅瘽鍒楄〃浠ユ洿鏂版秷鎭暟閲?    // 娉ㄦ剰锛氭秷鎭凡鍦?Agent Service 涓嚜鍔ㄤ繚瀛橈紝鏃犻渶鍓嶇鍐嶆淇濆瓨
    if (fullResponse && assistantMessageIndex !== -1) {
      await loadConversations()
    }

    isLoading.value = false

  } catch (err) {
    console.error('Error sending message:', err)
    error.value = err.message || 'Failed to send message. Please try again.'
    
    // Add error message
    messages.value.push({
      role: 'assistant',
      content: `<div class="error-message">
        <strong>Error:</strong> ${error.value}
        <br><br>
        Please make sure the backend server is running and the OpenAI API key is configured.
      </div>`,
      time: getCurrentTime()
    })
    
    isLoading.value = false
    
    await nextTick()
    scrollToBottom()
  }
}

const getCurrentTime = () => {
  const now = new Date()
  return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Auto-resize textarea
const autoResize = () => {
  if (inputTextarea.value) {
    inputTextarea.value.style.height = 'auto'
    inputTextarea.value.style.height = inputTextarea.value.scrollHeight + 'px'
  }
}

onMounted(async () => {
  if (inputTextarea.value) {
    inputTextarea.value.addEventListener('input', autoResize)
  }

  // 鍔犺浇瀵硅瘽鍒楄〃
  await loadConversations()

  if (window.innerWidth > 1024) {
    sidebarOpen.value = true
  }

  // Handle literature context from navigation
  if (route.query.context === 'literature') {
    const workInfo = history.state?.workInfo
    if (workInfo) {
      // Add context banner
      const contextMessage = `馃摎 Discussing paper: **${workInfo.title}**\n\n` +
        `*Authors:* ${workInfo.authors}\n` +
        `*Year:* ${workInfo.year || 'N/A'}\n` +
        `*Citations:* ${workInfo.citations || 0}\n\n` +
        `${workInfo.abstract ? `**Abstract:**\n${workInfo.abstract.substring(0, 300)}...` : ''}`
      
      const fullMessage = contextMessage + '\n\n---\n\nHow can I help you understand this paper?'
      const latexRendered = renderLatex(fullMessage)
      messages.value.push({
        role: 'assistant',
        content: marked.parse(latexRendered),
        time: getCurrentTime()
      })
    }
  }
})

onBeforeUnmount(() => {
  stopPaperLibraryPolling()
  chatMindmapInstances.clear()
})
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100vh;
  width: 100%;
  gap: 0;
  position: relative;
}

/* ============================================
   History Sidebar
   ============================================ */
.chat-sidebar {
  width: 280px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  flex-shrink: 0;
  z-index: 100;
  height: 100%;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px;
  border-bottom: 1px solid var(--border-primary);
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.sidebar-title svg {
  color: var(--accent-primary);
}

.sidebar-toggle {
  display: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-primary);
  color: var(--text-secondary);
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  color: var(--accent-primary);
  border-color: var(--border-glow);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 16px;
  padding: 12px 16px;
  background: var(--gradient-primary);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: var(--glow-primary);
}

.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.new-chat-btn svg {
  flex-shrink: 0;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 6px;
  border-radius: 10px;
  background: var(--bg-tertiary);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.conversation-item:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
  transform: translateX(4px);
}

.conversation-item.active {
  background: var(--gradient-primary);
  border-color: transparent;
  box-shadow: var(--glow-primary);
}

.conversation-item.active .conv-title,
.conversation-item.active .conv-meta {
  color: white;
}

.conv-content {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-meta {
  font-size: 11px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-delete {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(255, 107, 157, 0.1);
  border: 1px solid transparent;
  color: var(--accent-danger);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.conversation-item:hover .conv-delete {
  opacity: 1;
}

.conv-delete:hover {
  background: var(--accent-danger);
  color: white;
  border-color: var(--accent-danger);
}

.conversation-item.active .conv-delete {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.conversation-item.active:hover .conv-delete {
  background: rgba(255, 255, 255, 0.3);
}

.empty-conversations {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--text-tertiary);
}

.empty-conversations svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-conversations p {
  font-size: 13px;
  margin: 0;
}

.sidebar-overlay {
  display: none;
}

/* ============================================
   Chat Container
   ============================================ */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
  background:
    radial-gradient(circle at 74% 18%, rgba(168, 85, 247, 0.12), transparent 28%),
    linear-gradient(180deg, rgba(5, 8, 23, 0.18), rgba(5, 8, 23, 0.68));
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: min(1180px, calc(100% - 64px));
  margin: 0 auto 18px;
  padding: 28px 0 0;
  gap: 20px;
}

.paper-upload-notice {
  width: min(1180px, calc(100% - 64px));
  margin: 0 auto 16px;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  border: 1px solid var(--border-primary);
  background: rgba(15, 23, 42, 0.82);
  color: var(--text-primary);
}

.paper-upload-notice.success {
  border-color: rgba(34, 197, 94, 0.35);
  color: #86efac;
}

.paper-upload-notice.warning {
  border-color: rgba(250, 204, 21, 0.35);
  color: #fde68a;
}

.paper-upload-notice.error {
  border-color: rgba(244, 63, 94, 0.35);
  color: #fda4af;
}

.mobile-menu-btn {
  display: none;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  color: var(--text-secondary);
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
  margin-right: 12px;
}

.mobile-menu-btn:hover {
  color: var(--accent-primary);
  border-color: var(--border-glow);
}

.header-section {
  flex: 1;
  min-width: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 6px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 14px;
  background: rgba(8, 13, 28, 0.38);
  backdrop-filter: blur(14px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.16);
}

.paper-upload-input {
  display: none;
}

.header-action-btn {
  border: 1px solid var(--border-primary);
  background: rgba(15, 23, 42, 0.7);
  color: var(--text-primary);
  border-radius: 10px;
  padding: 10px 16px;
  min-height: 38px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.header-action-btn:hover:not(:disabled) {
  border-color: var(--border-glow);
  color: var(--accent-primary);
  box-shadow: var(--glow-primary);
}

.header-action-btn.secondary {
  background: rgba(5, 8, 23, 0.48);
}

.header-action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.attached-papers-bar {
  width: min(1180px, calc(100% - 64px));
  margin: 0 auto 16px;
  padding: 14px 16px;
  border-radius: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
}

.attached-papers-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
  margin-bottom: 10px;
}

.attached-papers-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.attached-paper-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
}

.attached-paper-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.attached-paper-name {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
}

.attached-paper-id {
  color: var(--text-tertiary);
  font-size: 11px;
}

.chip-remove-btn {
  border: none;
  background: transparent;
  color: var(--accent-danger);
  cursor: pointer;
  font-size: 12px;
}

.paper-library-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
  padding: 24px;
}

.paper-library-modal {
  width: min(720px, 100%);
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: 20px;
}

.paper-library-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 24px 24px 16px;
  border-bottom: 1px solid var(--border-primary);
}

.paper-library-header h3,
.paper-library-header p {
  margin: 0;
}

.paper-library-header p {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 14px;
}

.paper-library-close {
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.paper-library-list {
  padding: 16px 24px 24px;
  overflow-y: auto;
  display: grid;
  gap: 12px;
}

.paper-library-item {
  text-align: left;
  border: 1px solid var(--border-primary);
  background: var(--bg-card);
  border-radius: 14px;
  padding: 16px;
  cursor: pointer;
}

.paper-library-item:hover {
  border-color: var(--accent-primary);
}

.paper-library-item.disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.paper-library-item.disabled:hover {
  border-color: var(--border-primary);
}

.paper-library-title {
  color: var(--text-primary);
  font-weight: 600;
}

.paper-library-subtitle,
.paper-library-id,
.paper-library-empty,
.paper-library-error {
  color: var(--text-secondary);
  font-size: 13px;
}

.paper-library-notice {
  color: #fde68a;
  font-size: 13px;
  padding: 16px 24px 0;
}

.paper-library-subtitle,
.paper-library-id {
  margin-top: 6px;
}

.paper-library-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.paper-library-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid transparent;
}

.paper-library-status-badge.uploaded {
  background: rgba(148, 163, 184, 0.12);
  color: #cbd5e1;
  border-color: rgba(148, 163, 184, 0.22);
}

.paper-library-status-badge.indexing {
  background: rgba(250, 204, 21, 0.12);
  color: #fde68a;
  border-color: rgba(250, 204, 21, 0.28);
}

.paper-library-status-badge.indexed {
  background: rgba(34, 197, 94, 0.12);
  color: #86efac;
  border-color: rgba(34, 197, 94, 0.28);
}

.paper-library-status-badge.failed {
  background: rgba(244, 63, 94, 0.12);
  color: #fda4af;
  border-color: rgba(244, 63, 94, 0.28);
}

.paper-library-status-text {
  font-size: 12px;
  color: var(--text-secondary);
}

.paper-library-empty,
.paper-library-error {
  padding: 24px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  width: min(1180px, calc(100% - 64px));
  margin: 0 auto;
  padding: 0 0 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.empty-state {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  align-self: center;
  width: min(820px, 100%);
  min-height: 520px;
  margin: auto 0;
  text-align: center;
  padding: 40px 36px 24px;
  overflow: hidden;
}

.empty-state::before {
  content: '';
  position: absolute;
  inset: 8% 0 auto;
  width: 620px;
  height: 360px;
  margin: 0 auto;
  border-radius: 50%;
  pointer-events: none;
  background:
    radial-gradient(circle at 50% 46%, rgba(56, 189, 248, 0.2), transparent 34%),
    radial-gradient(circle at 50% 50%, rgba(168, 85, 247, 0.13), transparent 52%);
  filter: blur(4px);
  animation: coreAura 7s ease-in-out infinite;
}

.ai-logo-stage {
  position: relative;
  z-index: 1;
  width: 280px;
  height: 280px;
  margin-bottom: 22px;
  display: grid;
  place-items: center;
  perspective: 900px;
}

.empty-icon {
  position: relative;
  z-index: 1;
  width: 128px;
  height: 128px;
  border-radius: 50%;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow:
    0 0 42px rgba(56, 189, 248, 0.18),
    0 0 96px rgba(129, 140, 248, 0.18);
  transform: rotateX(10deg) rotateZ(-4deg);
  animation: logoFloat 5.6s ease-in-out infinite;
}

.empty-icon::before {
  content: '';
  position: absolute;
  inset: 10px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(103, 232, 249, 0.22), rgba(129, 140, 248, 0.12) 42%, transparent 70%);
  opacity: 0.82;
  filter: blur(16px);
  z-index: -1;
  animation: logoPulse 3.2s ease-in-out infinite;
}

.empty-icon svg {
  overflow: visible;
  filter: drop-shadow(0 0 12px rgba(255, 255, 255, 0.42));
}

.core-ring {
  stroke: rgba(226, 232, 240, 0.72);
  stroke-width: 1.8;
  fill: none;
  opacity: 0.92;
}

.core-ring-inner {
  stroke: rgba(125, 211, 252, 0.6);
  stroke-width: 1.4;
  opacity: 0.9;
}

.core-arc {
  stroke: rgba(255, 255, 255, 0.92);
  stroke-width: 3;
  stroke-linecap: round;
  fill: none;
  filter: drop-shadow(0 0 10px rgba(125, 211, 252, 0.32));
}

.core-arc-secondary {
  stroke: rgba(196, 181, 253, 0.88);
  filter: drop-shadow(0 0 10px rgba(196, 181, 253, 0.28));
}

.core-pulse {
  fill: #ffffff;
  filter:
    drop-shadow(0 0 12px rgba(255, 255, 255, 0.9))
    drop-shadow(0 0 28px rgba(103, 232, 249, 0.5));
  animation: coreSpark 3.4s ease-in-out infinite;
}

.logo-halo,
.logo-orbit,
.logo-reflection {
  position: absolute;
  pointer-events: none;
}

.logo-halo {
  inset: 34px;
  border-radius: 999px;
  border: 1px solid rgba(125, 211, 252, 0.18);
  box-shadow: inset 0 0 34px rgba(56, 189, 248, 0.08);
}

.halo-1 {
  animation: haloBreath 4.4s ease-in-out infinite;
}

.halo-2 {
  inset: 12px;
  border-color: rgba(196, 181, 253, 0.12);
  transform: rotateX(68deg);
  animation: haloTilt 7s linear infinite;
}

.logo-orbit {
  inset: 24px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  transform-style: preserve-3d;
}

.logo-orbit span {
  position: absolute;
  left: 50%;
  top: -4px;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #67e8f9;
  box-shadow: 0 0 18px rgba(103, 232, 249, 0.95);
}

.orbit-a {
  animation: orbitSpin 9s linear infinite;
}

.orbit-b {
  inset: 46px;
  transform: rotateX(68deg) rotateZ(22deg);
  animation: orbitSpinReverse 12s linear infinite;
}

.orbit-b span {
  background: #c4b5fd;
  box-shadow: 0 0 18px rgba(196, 181, 253, 0.95);
}

.orbit-c {
  inset: 70px;
  transform: rotateY(62deg) rotateZ(-18deg);
  animation: orbitSpin 7.5s linear infinite;
}

.orbit-c span {
  width: 6px;
  height: 6px;
  background: #34d399;
  box-shadow: 0 0 16px rgba(52, 211, 153, 0.85);
}

.logo-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.logo-particles span {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: rgba(186, 230, 253, 0.9);
  box-shadow: 0 0 12px rgba(125, 211, 252, 0.8);
  animation: particleDrift 4.8s ease-in-out infinite;
}

.logo-particles span:nth-child(1) { left: 20%; top: 26%; animation-delay: -0.4s; }
.logo-particles span:nth-child(2) { left: 78%; top: 30%; animation-delay: -1.1s; }
.logo-particles span:nth-child(3) { left: 15%; top: 66%; animation-delay: -2s; }
.logo-particles span:nth-child(4) { left: 84%; top: 68%; animation-delay: -2.7s; }
.logo-particles span:nth-child(5) { left: 48%; top: 12%; animation-delay: -3.2s; }
.logo-particles span:nth-child(6) { left: 52%; top: 88%; animation-delay: -3.9s; }

.logo-reflection {
  bottom: 20px;
  width: 156px;
  height: 26px;
  border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(56, 189, 248, 0.22), transparent 72%);
  filter: blur(3px);
  animation: reflectionPulse 5.6s ease-in-out infinite;
}

.empty-copy {
  position: relative;
  z-index: 1;
}

.empty-kicker {
  margin-bottom: 10px;
  color: var(--accent-primary);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.empty-state h3 {
  position: relative;
  z-index: 1;
  font-size: 30px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.empty-state p {
  position: relative;
  z-index: 1;
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 26px;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0) rotateX(10deg) rotateZ(-4deg); }
  50% { transform: translateY(-16px) rotateX(14deg) rotateZ(3deg); }
}

@keyframes logoPulse {
  0%, 100% { opacity: 0.62; transform: scale(1); }
  50% { opacity: 0.95; transform: scale(1.08); }
}

@keyframes haloBreath {
  0%, 100% { opacity: 0.38; transform: scale(0.92); }
  50% { opacity: 0.78; transform: scale(1.05); }
}

@keyframes haloTilt {
  from { transform: rotateX(68deg) rotateZ(0deg); }
  to { transform: rotateX(68deg) rotateZ(360deg); }
}

@keyframes orbitSpin {
  from { transform: rotateZ(0deg); }
  to { transform: rotateZ(360deg); }
}

@keyframes orbitSpinReverse {
  from { transform: rotateX(68deg) rotateZ(360deg); }
  to { transform: rotateX(68deg) rotateZ(0deg); }
}

@keyframes particleDrift {
  0%, 100% { opacity: 0.18; transform: translate3d(0, 0, 0) scale(0.7); }
  50% { opacity: 1; transform: translate3d(8px, -14px, 0) scale(1.2); }
}

@keyframes reflectionPulse {
  0%, 100% { opacity: 0.34; transform: scaleX(0.82); }
  50% { opacity: 0.62; transform: scaleX(1.08); }
}

@keyframes coreAura {
  0%, 100% { opacity: 0.72; transform: scale(0.96); }
  50% { opacity: 1; transform: scale(1.05); }
}

@keyframes coreSpark {
  0%, 100% { opacity: 0.86; transform: scale(0.96); }
  50% { opacity: 1; transform: scale(1.04); }
}

.message {
  display: flex;
  gap: 16px;
  width: min(920px, 100%);
  animation: fadeIn 0.3s ease;
}

.message-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-assistant {
  align-self: flex-start;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-user .message-avatar {
  background: var(--gradient-primary);
  color: white;
  box-shadow: var(--glow-primary);
}

.message-assistant .message-avatar {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-primary);
  color: var(--accent-primary);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-role {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.message-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.message-text {
  background: var(--bg-card);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  padding: 16px 20px;
  color: var(--text-primary);
  line-height: 1.7;
  font-size: 14px;
}

.message-user .message-text {
  background: var(--gradient-primary);
  color: white;
  border: none;
  box-shadow: var(--glow-primary);
}

/* Markdown Styles */
.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3) {
  color: var(--text-primary);
  margin: 16px 0 12px 0;
  font-weight: 600;
}

.message-text :deep(h1) { font-size: 24px; }
.message-text :deep(h2) { font-size: 20px; }
.message-text :deep(h3) { font-size: 16px; }

.message-text :deep(p) {
  margin: 12px 0;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.message-text :deep(li) {
  margin: 6px 0;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.message-text :deep(pre) {
  background: #282c34;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 16px 0;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
  color: #abb2bf;
}

.message-text :deep(blockquote) {
  border-left: 3px solid var(--accent-primary);
  padding-left: 16px;
  margin: 16px 0;
  color: var(--text-secondary);
  font-style: italic;
}

.message-text :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.message-text :deep(th),
.message-text :deep(td) {
  padding: 10px;
  border: 1px solid var(--border-primary);
  text-align: left;
}

.message-text :deep(th) {
  background: var(--bg-tertiary);
  font-weight: 600;
}

.message-text :deep(strong) {
  font-weight: 600;
  color: var(--accent-primary);
}

.message-user .message-text :deep(h1),
.message-user .message-text :deep(h2),
.message-user .message-text :deep(h3),
.message-user .message-text :deep(p),
.message-user .message-text :deep(li),
.message-user .message-text :deep(strong) {
  color: white;
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 16px 20px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-primary);
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

/* Chat Input */
.chat-input-container {
  padding: 14px 0 16px;
  border-top: 1px solid var(--border-primary);
  background: rgba(5, 8, 23, 0.52);
  backdrop-filter: blur(14px);
}

.chat-input-wrapper {
  display: flex;
  gap: 12px;
  align-items: center;
  width: min(1180px, calc(100% - 64px));
  margin: 0 auto;
  background: rgba(15, 23, 42, 0.74);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-primary);
  border-radius: 14px;
  padding: 9px 12px;
  transition: all 0.3s ease;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22);
}

.chat-input-wrapper:focus-within {
  border-color: var(--border-glow);
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.1), 0 18px 50px rgba(0, 0, 0, 0.26);
}

.input-plus-menu {
  position: relative;
  flex-shrink: 0;
}

.plus-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--border-primary);
  background: rgba(8, 13, 28, 0.78);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.plus-btn:hover:not(:disabled) {
  border-color: var(--accent-primary);
}

.plus-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.input-actions-popover {
  position: absolute;
  left: 0;
  bottom: calc(100% + 10px);
  min-width: 180px;
  padding: 8px;
  border-radius: 14px;
  border: 1px solid var(--border-primary);
  background: var(--bg-card);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.24);
  display: flex;
  flex-direction: column;
  gap: 6px;
  z-index: 20;
}

.input-action-item {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  color: var(--text-primary);
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
}

.input-action-item:hover {
  background: var(--bg-secondary);
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.5;
  resize: none;
  max-height: 200px;
  overflow-y: auto;
  font-family: inherit;
}

.chat-input::placeholder {
  color: var(--text-tertiary);
}

.chat-input:focus {
  outline: none;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--gradient-primary);
  border: none;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
  box-shadow: var(--glow-primary);
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 0 30px rgba(56, 189, 248, 0.5);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Scrollbar */
.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: var(--accent-primary);
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: var(--accent-secondary);
}

/* Error Message */
.error-message {
  color: var(--accent-danger);
  background: rgba(255, 107, 157, 0.1);
  padding: 12px;
  border-radius: 8px;
  border-left: 3px solid var(--accent-danger);
}

/* Agent Thinking & Tool Call - Modern Style */
.message-text :deep(.agent-thinking) {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
  font-size: 13px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.05));
  border-radius: 10px;
  margin-bottom: 12px;
  border: 1px solid rgba(102, 126, 234, 0.15);
  animation: thinkingPulse 2s ease-in-out infinite;
}

@keyframes thinkingPulse {
  0%, 100% { 
    border-color: rgba(102, 126, 234, 0.15);
    box-shadow: none;
  }
  50% { 
    border-color: rgba(102, 126, 234, 0.3);
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.1);
  }
}

.message-text :deep(.agent-tool-call) {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--accent-success);
  font-size: 12px;
  font-weight: 500;
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(78, 205, 196, 0.1), rgba(78, 205, 196, 0.05));
  border-radius: 8px;
  margin-bottom: 12px;
  border: 1px solid rgba(78, 205, 196, 0.2);
  font-family: 'SF Mono', 'Consolas', monospace;
}

.message-text :deep(.agent-tool-call::before) {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-success);
  box-shadow: 0 0 10px var(--accent-success);
  animation: toolPulse 1s ease-in-out infinite;
}

@keyframes toolPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.7; }
}

/* Papers Cards - Modern Design */
.message-text :deep(.papers-container) {
  margin: 20px 0;
  padding: 0;
}

.message-text :deep(.papers-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
}

.message-text :deep(.papers-header-left) {
  display: flex;
  align-items: center;
  gap: 12px;
}

.message-text :deep(.papers-icon-wrapper) {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: var(--glow-primary);
}

.message-text :deep(.papers-header-text) {
  display: flex;
  flex-direction: column;
}

.message-text :deep(.papers-count) {
  font-size: 24px;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.message-text :deep(.papers-label) {
  font-size: 12px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.message-text :deep(.papers-query-badge) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: 8px 14px;
  border-radius: 20px;
  border: 1px solid var(--border-primary);
}

.message-text :deep(.query-indicator) {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-success);
  box-shadow: 0 0 10px var(--accent-success);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.message-text :deep(.papers-grid) {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.message-text :deep(.paper-card) {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  animation: paperFadeIn 0.4s ease forwards;
  opacity: 0;
  transform: translateY(10px);
}

@keyframes paperFadeIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-text :deep(.paper-card-glow) {
  position: absolute;
  inset: 0;
  border-radius: 16px;
  padding: 1px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.1));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  transition: all 0.3s ease;
}

.message-text :deep(.paper-card:hover .paper-card-glow) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.6), rgba(118, 75, 162, 0.3));
  box-shadow: 0 0 30px rgba(102, 126, 234, 0.3);
}

.message-text :deep(.paper-card.hot-fire .paper-card-glow) {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.4), rgba(255, 165, 0, 0.2));
}

.message-text :deep(.paper-card.hot-fire:hover .paper-card-glow) {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.6), rgba(255, 165, 0, 0.4));
  box-shadow: 0 0 30px rgba(255, 107, 107, 0.3);
}

.message-text :deep(.paper-card-inner) {
  background: var(--bg-card);
  backdrop-filter: blur(10px);
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.message-text :deep(.paper-card-header) {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.message-text :deep(.paper-badges) {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.message-text :deep(.paper-badge) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.message-text :deep(.paper-badge-oa) {
  background: rgba(78, 205, 196, 0.15);
  color: var(--accent-success);
  border: 1px solid rgba(78, 205, 196, 0.3);
}

.message-text :deep(.paper-badge-hot) {
  background: rgba(255, 107, 107, 0.15);
  color: #ff6b6b;
  border: 1px solid rgba(255, 107, 107, 0.3);
}

.message-text :deep(.paper-year-badge) {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid var(--border-primary);
}

.message-text :deep(.paper-title) {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 10px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex-shrink: 0;
}

.message-text :deep(.paper-authors) {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0 0 10px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-text :deep(.paper-authors svg) {
  flex-shrink: 0;
  opacity: 0.6;
}

.message-text :deep(.paper-abstract) {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0 0 16px 0;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.message-text :deep(.paper-footer) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 14px;
  border-top: 1px solid var(--border-primary);
  margin-top: auto;
}

.message-text :deep(.paper-stats) {
  display: flex;
  gap: 16px;
}

.message-text :deep(.stat-item) {
  display: flex;
  align-items: center;
  gap: 6px;
}

.message-text :deep(.stat-item svg) {
  color: var(--accent-primary);
  opacity: 0.8;
}

.message-text :deep(.stat-value) {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.message-text :deep(.stat-label) {
  font-size: 11px;
  color: var(--text-tertiary);
}

.message-text :deep(.paper-link) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--accent-primary);
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.2);
  transition: all 0.3s ease;
}

.message-text :deep(.paper-link:hover) {
  background: var(--gradient-primary);
  color: white;
  border-color: transparent;
  box-shadow: var(--glow-primary);
  transform: translateY(-1px);
}

.message-text :deep(.papers-more) {
  text-align: center;
  margin-top: 16px;
  padding: 12px;
  background: var(--bg-secondary);
  border: 1px dashed var(--border-primary);
  border-radius: 10px;
  font-size: 13px;
  color: var(--text-tertiary);
}

.message-text :deep(.papers-empty) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  border: 1px dashed var(--border-primary);
  border-radius: 12px;
}

.message-text :deep(.papers-empty svg) {
  margin-bottom: 12px;
  opacity: 0.5;
}

.message-text :deep(.papers-empty p) {
  margin: 0;
  font-size: 14px;
}

.message-text :deep(.mindmap-card) {
  margin: 20px 0;
  padding: 18px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(14, 22, 48, 0.96), rgba(10, 16, 36, 0.96));
  border: 1px solid var(--border-primary);
}

.message-text :deep(.mindmap-card-header) {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

.message-text :deep(.mindmap-card-title) {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
}

.message-text :deep(.mindmap-card-subtitle) {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.message-text :deep(.mindmap-card-body) {
  overflow-x: auto;
}

.message-text :deep(.chat-jsmind-container) {
  width: 100%;
  min-width: 720px;
  height: 520px;
  overflow: auto;
  position: relative;
  background: #ffffff;
  border-radius: 14px;
}

.message-text :deep(.chat-jsmind-container .jsmind-inner) {
  background: #ffffff;
  font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
  width: 100%;
  height: 100%;
}

.message-text :deep(.chat-jsmind-container jmnode) {
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.message-text :deep(.chat-jsmind-container jmnode:hover) {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

/* Responsive for papers */
@media (max-width: 768px) {
  .message-text :deep(.papers-grid) {
    grid-template-columns: 1fr;
  }
  
  .message-text :deep(.papers-header) {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}

/* KaTeX Math Rendering */
.message-text :deep(.katex-block) {
  margin: 0.5rem 0;
  padding: 0.5rem 1rem;
  background: rgba(102, 126, 234, 0.05);
  border-left: 3px solid rgba(102, 126, 234, 0.5);
  border-radius: 4px;
  overflow-x: auto;
}

.message-text :deep(.katex) {
  font-size: 1.05em;
}

.message-text :deep(.katex-display) {
  margin: 0;
  text-align: center;
}

.message-text :deep(.katex-html) {
  color: var(--text-primary);
}

.message-text :deep(.katex-error) {
  display: none;
}

.message-text :deep(.katex-mathml) {
  display: none;
}

/* Responsive */
@media (max-width: 1024px) {
  .chat-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    transform: translateX(-100%);
    z-index: 1000;
  }

  .chat-sidebar.sidebar-open {
    transform: translateX(0);
  }

  .sidebar-toggle {
    display: flex;
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(4px);
    z-index: 999;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
  }

  .sidebar-overlay.active {
    opacity: 1;
    pointer-events: all;
  }

  .mobile-menu-btn {
    display: flex;
  }

  .chat-header {
    width: min(100% - 40px, 920px);
    padding: 18px 0 0;
  }

  .paper-upload-notice {
    width: min(100% - 40px, 920px);
  }

  .chat-messages {
    width: min(100% - 40px, 920px);
    padding: 0 0 20px;
  }

  .chat-input-container {
    padding: 14px 0;
  }

  .chat-input-wrapper {
    width: min(100% - 40px, 920px);
  }

  .attached-papers-bar {
    width: min(100% - 40px, 920px);
  }
}

@media (max-width: 768px) {
  .chat-header {
    flex-direction: column;
    width: calc(100% - 32px);
    padding: 14px 0 0;
    gap: 14px;
  }

  .paper-upload-notice {
    width: calc(100% - 32px);
  }

  .header-actions {
    width: 100%;
    justify-content: stretch;
  }

  .header-action-btn {
    flex: 1;
    padding-inline: 10px;
  }

  .message {
    gap: 12px;
    width: 100%;
  }

  .message-avatar {
    width: 36px;
    height: 36px;
  }

  .message-text {
    padding: 12px 16px;
    font-size: 13px;
  }

  .message-text :deep(.katex-block) {
    padding: 0.4rem 0.75rem;
    font-size: 0.9em;
  }
  
  .message-text :deep(.katex) {
    font-size: 1em;
  }

  .chat-messages {
    width: calc(100% - 32px);
    padding: 0 0 16px;
  }

  .empty-state {
    min-height: 320px;
    padding: 32px 20px;
  }

  .ai-logo-stage {
    width: 220px;
    height: 220px;
    margin-bottom: 14px;
  }

  .empty-icon {
    width: 104px;
    height: 104px;
    border-radius: 28px;
  }

  .empty-icon svg {
    width: 60px;
    height: 60px;
  }

  .empty-state h3 {
    font-size: 25px;
  }

  .chat-input-container {
    padding: 12px 0;
  }

  .chat-input-wrapper {
    width: calc(100% - 32px);
  }

  .attached-papers-bar {
    width: calc(100% - 32px);
  }

  .new-chat-btn span {
    display: none;
  }

  .new-chat-btn {
    width: 48px;
    justify-content: center;
  }

  .conv-meta {
    font-size: 10px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .empty-icon,
  .empty-icon::before,
  .logo-halo,
  .logo-orbit,
  .logo-particles span,
  .logo-reflection,
  .empty-state::before {
    animation: none;
  }
}

/* Scrollbar for sidebar */
.conversation-list::-webkit-scrollbar {
  width: 6px;
}

.conversation-list::-webkit-scrollbar-track {
  background: transparent;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: var(--accent-primary);
  border-radius: 3px;
}

.conversation-list::-webkit-scrollbar-thumb:hover {
  background: var(--accent-secondary);
}
</style>

