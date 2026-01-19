<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="header-section">
        <h1 class="page-title">AI Research Assistant</h1>
        <p class="page-subtitle">Ask me anything about your research</p>
      </div>
      <div class="header-actions">
        <!-- 预留操作按钮位置，暂时为空 -->
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </div>
        <h3>Start a Conversation</h3>
        <p>Ask me about research papers, concepts, or anything else you'd like to know.</p>
        <div class="suggested-prompts">
          <button v-for="prompt in suggestedPrompts" :key="prompt" class="prompt-btn" @click="sendSuggestedPrompt(prompt)">
            {{ prompt }}
          </button>
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
</template>

<script>
export default {
  name: 'Chat'
}
</script>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import katex from 'katex'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'
import 'katex/dist/katex.min.css'
import { API_ENDPOINTS } from '../config'

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
const error = ref(null)

const suggestedPrompts = ref([
  'Explain transformer architecture',
  'Summarize recent advances in LLMs',
  'How does attention mechanism work?',
  'Compare CNNs and Vision Transformers'
])

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

const sendSuggestedPrompt = (prompt) => {
  inputMessage.value = prompt
  sendMessage()
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage = {
    role: 'user',
    content: inputMessage.value,
    time: getCurrentTime()
  }

  messages.value.push(userMessage)
  const userInput = inputMessage.value
  inputMessage.value = ''

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

    // Create placeholder for assistant message
    const assistantMessageIndex = messages.value.length
    messages.value.push({
      role: 'assistant',
      content: '',
      time: getCurrentTime()
    })

    await nextTick()
    scrollToBottom()

    // Call API with SSE
    const response = await fetch(API_ENDPOINTS.CHAT_MESSAGE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: userInput,
        conversation_history: conversationHistory.slice(0, -1), // Exclude the current message
        stream: true,
        temperature: 0.7,
        max_tokens: 2000
      })
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }

    // Read SSE stream
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullResponse = ''

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          
          if (data === '[DONE]') continue

          try {
            const parsed = JSON.parse(data)
            
            if (parsed.content) {
              fullResponse += parsed.content
              // Render LaTeX first, then markdown
              const latexRendered = renderLatex(fullResponse)
              messages.value[assistantMessageIndex].content = marked(latexRendered)
              
              await nextTick()
              scrollToBottom()
            }
            
            if (parsed.error) {
              throw new Error(parsed.error)
            }
          } catch (e) {
            if (e instanceof SyntaxError) {
              // Ignore JSON parsing errors for incomplete chunks
              continue
            }
            throw e
          }
        }
      }
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

onMounted(() => {
  if (inputTextarea.value) {
    inputTextarea.value.addEventListener('input', autoResize)
  }

  // Handle literature context from navigation
  if (route.query.context === 'literature') {
    const workInfo = history.state?.workInfo
    if (workInfo) {
      // Add context banner
      const contextMessage = `📚 Discussing paper: **${workInfo.title}**\n\n` +
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
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
  max-width: 1600px;
  margin: 0 auto -20px;
}

.chat-header {
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

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
  padding: 40px;
}

.empty-icon {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: var(--glow-primary);
}

.empty-icon svg {
  color: white;
}

.empty-state h3 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.empty-state p {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.suggested-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  max-width: 600px;
}

.prompt-btn {
  padding: 10px 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 20px;
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.prompt-btn:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
  transform: translateY(-2px);
}

.message {
  display: flex;
  gap: 16px;
  animation: fadeIn 0.3s ease;
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
  padding-top: 16px;
  border-top: 1px solid var(--border-primary);
}

.chat-input-wrapper {
  display: flex;
  gap: 12px;
  align-items: center;
  background: var(--bg-card);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  padding: 8px 12px;
  transition: all 0.3s ease;
}

.chat-input-wrapper:focus-within {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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
  box-shadow: 0 0 30px rgba(102, 126, 234, 0.8);
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
@media (max-width: 768px) {
  .chat-container {
    height: calc(100vh - 32px);
  }

  .chat-header {
    flex-direction: column;
  }

  .message {
    gap: 12px;
  }

  .message-avatar {
    width: 36px;
    height: 36px;
  }

  .message-text {
    padding: 12px 16px;
    font-size: 13px;
  }

  .suggested-prompts {
    flex-direction: column;
  }

  .prompt-btn {
    width: 100%;
  }
  
  .message-text :deep(.katex-block) {
    padding: 0.4rem 0.75rem;
    font-size: 0.9em;
  }
  
  .message-text :deep(.katex) {
    font-size: 1em;
  }
}
</style>

