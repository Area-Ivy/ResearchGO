<template>
  <div class="review-container">
    <!-- Header -->
    <div class="review-header">
      <div class="header-section">
        <h1 class="page-title">Paper Analysis Workspace</h1>
        <p class="page-subtitle">AI-powered multi-dimensional paper understanding system</p>
      </div>
      <div class="header-actions">
        <button 
          @click="showPaperList = true" 
          class="btn btn-primary"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
          <span>{{ selectedPaper ? 'Switch Paper' : 'Select Paper' }}</span>
        </button>
      </div>
    </div>

    <!-- 论文选择对话框 -->
    <div v-if="showPaperList" class="modal-overlay" @click="showPaperList = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>选择论文</h2>
          <button @click="showPaperList = false" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="loading" class="loading">
            <div class="loading-spinner"></div>
            <p class="loading-text">Loading papers...</p>
          </div>
          <div v-else-if="papers.length === 0" class="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
            </svg>
            <h3>No Papers Available</h3>
            <p>Upload papers to your library first</p>
            <router-link to="/library" class="btn-primary">Go to Library</router-link>
          </div>
          <div v-else class="paper-list">
            <div 
              v-for="paper in papers" 
              :key="paper.object_name"
              class="paper-item"
              @click="selectPaper(paper)"
            >
              <div class="paper-icon">📄</div>
              <div class="paper-info">
                <h3>{{ paper.original_name }}</h3>
                <p class="paper-meta">
                  大小: {{ formatSize(paper.size) }} | 
                  上传时间: {{ formatDate(paper.last_modified) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 - 始终显示左右布局 -->
    <div class="content-wrapper">
      <!-- 左侧：PDF阅读器 -->
      <div class="pdf-viewer-panel">
        <div class="pdf-viewer">
          <iframe 
            v-if="pdfUrl"
            :src="pdfUrl" 
            class="pdf-iframe"
            frameborder="0"
          ></iframe>
          <div v-else class="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.3;">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
            </svg>
            <h3>No PDF Selected</h3>
            <p>Please select a paper from the list to view its content.</p>
            <button @click="showPaperList = true" class="btn-primary">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
              <span>Select Paper</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧：功能面板 -->
      <div class="feature-panel">
        <!-- 功能标签栏 -->
        <div class="feature-tabs">
          <button 
            v-for="tab in featureTabs" 
            :key="tab.id"
            :class="['feature-tab', { active: activeTab === tab.id }]"
            @click="activeTab = tab.id"
          >
            <span class="tab-icon" v-html="tab.icon"></span>
            <span class="tab-label">{{ tab.label }}</span>
          </button>
        </div>

        <!-- 功能内容区 -->
        <div class="feature-content">
          <!-- 思维导图 -->
          <div v-show="activeTab === 'mindmap'" class="feature-view">
            <div class="feature-header">
              <div class="feature-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"></path>
                </svg>
                <h3>Paper Mind Map</h3>
                <span class="badge badge-primary" v-if="mindmapGenerated">Generated</span>
              </div>
              <div class="feature-controls">
                <button 
                  v-if="!mindmapGenerated" 
                  @click="generateMindmap" 
                  :disabled="generatingMindmap"
                  class="btn btn-primary btn-sm"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-if="!generatingMindmap">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                  </svg>
                  <span>{{ generatingMindmap ? 'Generating...' : 'Generate Map' }}</span>
                </button>
                <button 
                  v-if="mindmapGenerated" 
                  @click="regenerateMindmap" 
                  :disabled="generatingMindmap"
                  class="btn btn-secondary btn-sm"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="1 4 1 10 7 10"></polyline>
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
                  </svg>
                  <span>Regenerate</span>
                </button>
              </div>
            </div>
            <div class="feature-body">
              <div ref="mindmapContainer" class="jsmind-container" v-show="mindmapGenerated"></div>
              <div v-if="generatingMindmap" class="loading-overlay">
                <div class="spinner"></div>
                <p>AI正在分析论文并生成思维导图...</p>
                <p style="font-size: 12px; color: var(--text-tertiary); margin-top: 8px;">预计需要10-30秒</p>
              </div>
              <div v-else-if="!mindmapGenerated" class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.3;">
                  <circle cx="12" cy="12" r="2"></circle>
                  <path d="M12 2v4"></path>
                  <path d="M12 18v4"></path>
                  <path d="m4.93 4.93 2.83 2.83"></path>
                  <path d="m16.24 16.24 2.83 2.83"></path>
                  <path d="M2 12h4"></path>
                  <path d="M18 12h4"></path>
                  <path d="m4.93 19.07 2.83-2.83"></path>
                  <path d="m16.24 7.76 2.83-2.83"></path>
                </svg>
                <h3 style="color: var(--text-primary); margin: 16px 0 8px;">准备生成</h3>
                <p style="color: var(--text-secondary);">点击"生成思维导图"开始AI分析</p>
              </div>
            </div>
          </div>

          <!-- 分析 -->
          <div v-show="activeTab === 'analysis'" class="feature-view">
            <div class="feature-header">
              <div class="feature-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 3v18h18"></path>
                  <path d="m19 9-5 5-4-4-3 3"></path>
                </svg>
                <h3>Paper Analysis</h3>
                <span class="badge badge-primary" v-if="analysisGenerated">Generated</span>
              </div>
              <div class="feature-controls">
                <button 
                  v-if="!analysisGenerated" 
                  @click="generateAnalysis" 
                  :disabled="generatingAnalysis || !selectedPaper"
                  class="btn btn-primary btn-sm"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-if="!generatingAnalysis">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                  </svg>
                  <span>{{ generatingAnalysis ? 'Analyzing...' : 'Generate Analysis' }}</span>
                </button>
                <button 
                  v-if="analysisGenerated" 
                  @click="regenerateAnalysis" 
                  :disabled="generatingAnalysis"
                  class="btn btn-secondary btn-sm"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="1 4 1 10 7 10"></polyline>
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
                  </svg>
                  <span>Regenerate</span>
                </button>
              </div>
            </div>
            <div class="feature-body">
              <div v-if="generatingAnalysis" class="loading-overlay">
                <div class="spinner"></div>
                <p>AI正在深度分析论文...</p>
                <p style="font-size: 12px; color: var(--text-tertiary); margin-top: 8px;">预计需要20-60秒</p>
              </div>
              <div v-else-if="analysisGenerated && analysisData" class="analysis-content">
                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                    <h4>论文标题</h4>
                  </div>
                  <p class="section-content highlight-title">{{ analysisData.title }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M4 7h16M4 12h16M4 17h10"></path>
                    </svg>
                    <h4>摘要</h4>
                  </div>
                  <p class="section-content">{{ analysisData.abstract }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <path d="M12 16v-4M12 8h.01"></path>
                    </svg>
                    <h4>研究背景</h4>
                  </div>
                  <p class="section-content">{{ analysisData.research_background }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01"></path>
                    </svg>
                    <h4>研究问题</h4>
                  </div>
                  <p class="section-content">{{ analysisData.research_problem }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                      <path d="M2 17l10 5 10-5M2 12l10 5 10-5"></path>
                    </svg>
                    <h4>研究方法</h4>
                  </div>
                  <p class="section-content">{{ analysisData.methodology }}</p>
                </div>

                <div class="analysis-section highlight">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M3 3v18h18"></path>
                      <path d="m19 9-5 5-4-4-3 3"></path>
                    </svg>
                    <h4>主要发现</h4>
                  </div>
                  <p class="section-content">{{ analysisData.key_findings }}</p>
                </div>

                <div class="analysis-section highlight">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path>
                    </svg>
                    <h4>创新点</h4>
                  </div>
                  <p class="section-content">{{ analysisData.innovations }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                      <line x1="12" y1="9" x2="12" y2="13"></line>
                      <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    <h4>局限性</h4>
                  </div>
                  <p class="section-content">{{ analysisData.limitations }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="12" y1="18" x2="12" y2="12"></line>
                      <line x1="9" y1="15" x2="15" y2="15"></line>
                    </svg>
                    <h4>未来工作</h4>
                  </div>
                  <p class="section-content">{{ analysisData.future_work }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="9 11 12 14 22 4"></polyline>
                      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                    </svg>
                    <h4>结论</h4>
                  </div>
                  <p class="section-content">{{ analysisData.conclusion }}</p>
                </div>
              </div>
              <div v-else class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.3;">
                  <path d="M3 3v18h18"></path>
                  <path d="m19 9-5 5-4-4-3 3"></path>
                </svg>
                <h3 style="color: var(--text-primary); margin: 16px 0 8px;">准备分析</h3>
                <p style="color: var(--text-secondary);">{{ selectedPaper ? '点击"生成分析"开始AI分析' : '请先选择一篇论文' }}</p>
              </div>
            </div>
          </div>

          <!-- 关系图谱 -->
          <div v-show="activeTab === 'graph'" class="feature-view">
            <div class="feature-header">
              <div class="feature-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="2"></circle>
                  <circle cx="6" cy="6" r="2"></circle>
                  <circle cx="18" cy="6" r="2"></circle>
                  <circle cx="6" cy="18" r="2"></circle>
                  <circle cx="18" cy="18" r="2"></circle>
                </svg>
                <h3>Citation Graph</h3>
                <span class="badge badge-secondary">Coming Soon</span>
              </div>
            </div>
            <div class="feature-body">
              <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.3;">
                  <circle cx="12" cy="12" r="3"></circle>
                  <circle cx="6" cy="6" r="2"></circle>
                  <circle cx="18" cy="6" r="2"></circle>
                  <circle cx="6" cy="18" r="2"></circle>
                  <circle cx="18" cy="18" r="2"></circle>
                  <path d="M12 9V6"></path>
                  <path d="M10.5 10.5 6 6"></path>
                  <path d="M13.5 10.5 18 6"></path>
                  <path d="M10.5 13.5 6 18"></path>
                  <path d="M13.5 13.5 18 18"></path>
                </svg>
                <h3>即将推出</h3>
                <p>论文引用关系星图功能开发中...</p>
              </div>
            </div>
          </div>

          <!-- AI助手 -->
          <div v-show="activeTab === 'assistant'" class="feature-view">
            <div class="feature-header">
              <div class="feature-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  <line x1="9" y1="9" x2="15" y2="9"></line>
                  <line x1="9" y1="13" x2="12" y2="13"></line>
                </svg>
                <h3>AI Assistant</h3>
                <span class="badge badge-secondary">Coming Soon</span>
              </div>
            </div>
            <div class="feature-body">
              <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.3;">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  <path d="M8 10h.01"></path>
                  <path d="M12 10h.01"></path>
                  <path d="M16 10h.01"></path>
                </svg>
                <h3>即将推出</h3>
                <p>AI问答助手功能开发中...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { listPapers, downloadPaper } from '../api/papers'
import { generateMindmap as generateMindmapAPI } from '../api/mindmap'
import { generateAnalysis as generateAnalysisAPI } from '../api/analysis'
import jsMind from 'jsmind'
import 'jsmind/style/jsmind.css'
import { API_BASE_URL } from '../config'

export default {
  name: 'PaperReview',
  setup() {
    // 状态管理
    const loading = ref(false)
    const papers = ref([])
    const selectedPaper = ref(null)
    const showPaperList = ref(false)
    
    // PDF相关
    const pdfUrl = ref('')
    
    // 功能标签
    const activeTab = ref('mindmap')
    const featureTabs = [
      { 
        id: 'mindmap', 
        label: 'Mind Map',
        icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"></path>
        </svg>`
      },
      { 
        id: 'analysis', 
        label: 'Analysis',
        icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 3v18h18"></path>
          <path d="m19 9-5 5-4-4-3 3"></path>
        </svg>`
      },
      { 
        id: 'graph', 
        label: 'Citation Graph',
        icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="2"></circle>
          <circle cx="6" cy="6" r="2"></circle>
          <circle cx="18" cy="6" r="2"></circle>
          <circle cx="6" cy="18" r="2"></circle>
          <circle cx="18" cy="18" r="2"></circle>
          <line x1="12" y1="14" x2="12" y2="10"></line>
          <line x1="10.5" y1="10.5" x2="7.5" y2="7.5"></line>
          <line x1="13.5" y1="10.5" x2="16.5" y2="7.5"></line>
          <line x1="10.5" y1="13.5" x2="7.5" y2="16.5"></line>
          <line x1="13.5" y1="13.5" x2="16.5" y2="16.5"></line>
        </svg>`
      },
      { 
        id: 'assistant', 
        label: 'AI Assistant',
        icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          <line x1="9" y1="9" x2="15" y2="9"></line>
          <line x1="9" y1="13" x2="12" y2="13"></line>
        </svg>`
      }
    ]
    
    // 思维导图相关
    const mindmapContainer = ref(null)
    const generatingMindmap = ref(false)
    const mindmapGenerated = ref(false)
    const mindmapData = ref(null)
    let jsMindInstance = null

    // 分析相关
    const generatingAnalysis = ref(false)
    const analysisGenerated = ref(false)
    const analysisData = ref(null)

    // 加载论文列表
    const loadPapers = async () => {
      loading.value = true
      try {
        const response = await listPapers()
        papers.value = response.papers || []
      } catch (error) {
        console.error('Failed to load papers:', error)
        alert('加载论文列表失败')
      } finally {
        loading.value = false
      }
    }

    // 选择论文
    const selectPaper = (paper) => {
      selectedPaper.value = paper
      showPaperList.value = false
      // 使用view端点而不是download，这样浏览器会在线显示而不是下载
      pdfUrl.value = `${API_BASE_URL}/api/papers/view/${paper.object_name}`
    }

    // 重置选择
    const resetSelection = () => {
      selectedPaper.value = null
      pdfUrl.value = ''
      mindmapGenerated.value = false
      mindmapData.value = null
      analysisGenerated.value = false
      analysisData.value = null
      
      // 清空思维导图
      if (jsMindInstance) {
        jsMindInstance = null
      }
      if (mindmapContainer.value) {
        mindmapContainer.value.innerHTML = ''
      }
    }

    // 生成思维导图
    const generateMindmap = async () => {
      if (!selectedPaper.value) return
      
      generatingMindmap.value = true
      try {
        const result = await generateMindmapAPI(
          selectedPaper.value.object_name,
          3,
          'zh'
        )
        
        if (result.success) {
          if (!result.mindmap_data) {
            throw new Error('后端返回的思维导图数据为空')
          }
          console.log('Received mindmap data:', result.mindmap_data)
          mindmapData.value = result.mindmap_data
          await renderMindmap(result.mindmap_data)
          mindmapGenerated.value = true
        } else {
          throw new Error(result.message || '生成思维导图失败')
        }
      } catch (error) {
        console.error('Failed to generate mindmap:', error)
        alert('生成思维导图失败：' + (error.response?.data?.detail || error.message))
      } finally {
        generatingMindmap.value = false
      }
    }

    // 重新生成思维导图
    const regenerateMindmap = async () => {
      mindmapGenerated.value = false
      mindmapData.value = null
      if (jsMindInstance) {
        markmapInstance.value.destroy()
        markmapInstance.value = null
      }
      await generateMindmap()
    }

    // 添加缩放功能（滚动条位置保持不变）
    const addDragAndZoom = (container) => {
      let scale = 1
      
      const jsmindInner = container.querySelector('.jsmind-inner')
      if (!jsmindInner) return
      
      // 设置初始样式
      jsmindInner.style.transformOrigin = '0 0'
      jsmindInner.style.transition = 'transform 0.2s ease-out'
      
      // 滚轮缩放 - 按住Ctrl键时缩放，否则正常滚动
      container.addEventListener('wheel', (e) => {
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault()
          
          // 记录缩放前的滚动位置和鼠标位置
          const rect = container.getBoundingClientRect()
          const mouseX = e.clientX - rect.left
          const mouseY = e.clientY - rect.top
          
          // 计算鼠标相对于容器内容的位置（考虑当前滚动和缩放）
          const scrollLeft = container.scrollLeft
          const scrollTop = container.scrollTop
          const contentX = (mouseX + scrollLeft) / scale
          const contentY = (mouseY + scrollTop) / scale
          
          // 计算新的缩放比例
          const delta = e.deltaY > 0 ? 0.9 : 1.1
          const newScale = Math.min(Math.max(scale * delta, 0.5), 2)
          
          // 应用缩放
          scale = newScale
          jsmindInner.style.transform = `scale(${scale})`
          
          // 调整滚动位置，使鼠标指向的内容位置保持不变
          container.scrollLeft = contentX * scale - mouseX
          container.scrollTop = contentY * scale - mouseY
        }
        // 不按Ctrl键时，允许正常滚动
      }, { passive: false })
      
      // 双击重置
      container.addEventListener('dblclick', (e) => {
        if (e.target === container || e.target.classList.contains('jsmind-inner')) {
          // 记录当前中心位置
          const scrollLeft = container.scrollLeft
          const scrollTop = container.scrollTop
          const centerX = (scrollLeft + container.clientWidth / 2) / scale
          const centerY = (scrollTop + container.clientHeight / 2) / scale
          
          scale = 1
          jsmindInner.style.transition = 'transform 0.3s ease'
          jsmindInner.style.transform = 'scale(1)'
          
          // 调整滚动位置以保持中心点不变
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
    
    // 渲染思维导图
    const renderMindmap = async (data) => {
      await nextTick()
      
      const container = mindmapContainer.value
      if (!container) {
        console.error('Container not found')
        return
      }
      
      try {
        console.log('Rendering jsMind with data:', data)
        
        // 清理之前的实例
        if (jsMindInstance) {
          jsMindInstance = null
        }
        
        // 清空容器
        container.innerHTML = ''
        
        // 创建jsMind配置
        const options = {
          container: container,
          theme: 'primary',
          editable: false,
          view: {
            engine: 'canvas',
            hmargin: 100,
            vmargin: 50,
            line_width: 2,
            line_color: '#555'
          }
        }
        
        // 创建jsMind实例
        jsMindInstance = new jsMind(options)
        jsMindInstance.show(data)
        
        // 添加拖动和缩放功能
        addDragAndZoom(container)
        
        console.log('jsMind rendered successfully with drag & zoom')
      } catch (error) {
        console.error('Failed to render jsMind:', error)
        alert('渲染思维导图失败: ' + error.message)
      }
    }

    // 生成分析
    const generateAnalysis = async () => {
      if (!selectedPaper.value) return
      
      generatingAnalysis.value = true
      try {
        const result = await generateAnalysisAPI(
          selectedPaper.value.object_name,
          'zh'
        )
        
        if (result.success) {
          if (!result.analysis) {
            throw new Error('后端返回的分析数据为空')
          }
          console.log('Received analysis data:', result.analysis)
          analysisData.value = result.analysis
          analysisGenerated.value = true
        } else {
          throw new Error(result.message || '生成分析失败')
        }
      } catch (error) {
        console.error('Failed to generate analysis:', error)
        alert('生成分析失败：' + (error.response?.data?.detail || error.message))
      } finally {
        generatingAnalysis.value = false
      }
    }

    // 重新生成分析
    const regenerateAnalysis = async () => {
      analysisGenerated.value = false
      analysisData.value = null
      await generateAnalysis()
    }

    // 格式化文件大小
    const formatSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    }

    // 格式化日期
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    // 生命周期
    onMounted(() => {
      loadPapers()
    })

    onUnmounted(() => {
      // 清理思维导图
      if (jsMindInstance) {
        jsMindInstance = null
      }
    })

    return {
      loading,
      papers,
      selectedPaper,
      showPaperList,
      pdfUrl,
      activeTab,
      featureTabs,
      mindmapContainer,
      generatingMindmap,
      mindmapGenerated,
      generatingAnalysis,
      analysisGenerated,
      analysisData,
      selectPaper,
      resetSelection,
      generateMindmap,
      regenerateMindmap,
      generateAnalysis,
      regenerateAnalysis,
      formatSize,
      formatDate
    }
  }
}
</script>

<style scoped>
.review-container {
  max-width: 1600px;
  margin: 0 auto;
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
}

/* Header */
.review-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
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

/* 按钮样式 */
.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
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
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
  border: 1px solid var(--border-primary);
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
}

.btn-large {
  padding: 12px 32px;
  font-size: 16px;
}


.btn-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-close:hover {
  background: rgba(255, 107, 157, 0.1);
  border-color: var(--accent-danger);
  color: var(--accent-danger);
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-glow);
  border-radius: 16px;
  box-shadow: var(--shadow-lg);
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 24px;
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

/* 论文列表 */
.paper-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.paper-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.paper-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(102, 126, 234, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
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
  font-size: 1.5rem;
}

.paper-info {
  flex: 1;
  min-width: 0;
}

.paper-info h3 {
  margin: 0 0 8px 0;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.paper-meta {
  margin: 0;
  font-size: 13px;
  color: var(--text-tertiary);
}

/* 主要内容区域 */
.content-wrapper {
  flex: 1;
  display: flex;
  gap: 20px;
  overflow: hidden;
}

.pdf-viewer-panel,
.feature-panel {
  flex: 1;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 功能标签栏 */
.feature-tabs {
  display: flex;
  background: rgba(0, 0, 0, 0.15);
  padding: 10px;
  gap: 6px;
  border-bottom: 1px solid var(--border-primary);
}

.feature-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 13px;
  font-weight: 600;
  position: relative;
  overflow: hidden;
}

.feature-tab::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 0;
}

.feature-tab:hover::before {
  opacity: 1;
}

.feature-tab:hover {
  color: var(--text-primary);
  transform: translateY(-1px);
}

.feature-tab.active {
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4), 0 2px 8px rgba(139, 92, 246, 0.2);
  transform: translateY(-2px);
}

.feature-tab.active::before {
  opacity: 0;
}

.tab-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.tab-icon :deep(svg) {
  transition: transform 0.3s ease;
}

.feature-tab.active .tab-icon :deep(svg) {
  transform: scale(1.1);
}

.tab-label {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.3px;
  position: relative;
  z-index: 1;
}

/* 功能内容区 */
.feature-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.feature-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.feature-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.02);
}

.feature-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.feature-title svg {
  color: var(--accent-primary);
}

.feature-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-title svg {
  color: var(--accent-primary);
}

.panel-title h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 徽章样式 */
.badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-primary {
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.badge-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.feature-body {
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.btn:hover {
  transform: translateY(-2px);
}

.btn:active {
  transform: translateY(0);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-primary {
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}

.btn-primary:hover:not(:disabled) {
  box-shadow: 0 6px 24px rgba(99, 102, 241, 0.4);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

.btn-sm {
  padding: 8px 16px;
  font-size: 13px;
}

.btn svg {
  flex-shrink: 0;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.02);
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.mindmap-controls {
  display: flex;
  gap: 8px;
}

/* PDF阅读器 */
.pdf-viewer {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
  background: rgba(0, 0, 0, 0.2);
}

.pdf-viewer .empty-state {
  width: 100%;
  max-width: 400px;
  padding: 60px 40px;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

/* 思维导图容器 */
.jsmind-container {
  width: 100%;
  height: 100%;
  overflow: auto;
  cursor: default;
  position: relative;
  background: #ffffff;
}

/* jsMind样式优化 */
:deep(.jsmind-inner) {
  background: #ffffff;
  font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
  width: 100%;
  height: 100%;
}

:deep(jmnode) {
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

:deep(jmnode:hover) {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

/* 加载和空状态 */
.loading,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  text-align: center;
  gap: 16px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(102, 126, 234, 0.2);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}

.empty-state svg {
  color: var(--accent-primary);
  opacity: 0.4;
  filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.2));
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 12px 0 8px 0;
  letter-spacing: 0.3px;
}

.empty-state p {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 24px 0;
  max-width: 320px;
}

.empty-state .btn-primary {
  margin-top: 8px;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(19, 24, 41, 0.95);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.loading-overlay p {
  margin-top: 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(102, 126, 234, 0.2);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.empty-state-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px;
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin-bottom: 24px;
  color: var(--text-tertiary);
  opacity: 0.3;
}

.empty-state-main h2 {
  margin: 16px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state-main p {
  margin: 0 0 32px 0;
  font-size: 16px;
  color: var(--text-secondary);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .review-header {
    flex-direction: column;
  }

  .content-wrapper {
    flex-direction: column;
  }
  
  .pdf-viewer-panel,
  .feature-panel {
    height: 50vh;
    min-height: 400px;
  }
}

@media (max-width: 768px) {
  .review-container {
    height: auto;
  }

  .header-actions {
    width: 100%;
  }

  .btn-primary,
  .btn-secondary {
    flex: 1;
  }

  .content-wrapper {
    gap: 16px;
  }

  .pdf-viewer-panel,
  .feature-panel {
    height: 400px;
  }

  .modal-content {
    width: 95%;
    max-height: 90vh;
  }

  .paper-list {
    gap: 8px;
  }

  .paper-item {
    padding: 12px;
  }
}

/* 分析内容样式 */
.analysis-content {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  background: rgba(0, 0, 0, 0.2);
}

.analysis-section {
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.analysis-section:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.2);
  transform: translateY(-2px);
}

.analysis-section.highlight {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.analysis-section.highlight:hover {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  border-color: rgba(99, 102, 241, 0.5);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 2px solid rgba(99, 102, 241, 0.2);
}

.section-header svg {
  color: var(--accent-primary);
  flex-shrink: 0;
}

.section-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

.section-content {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.highlight-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.6;
}

/* 滚动条样式 */
.analysis-content::-webkit-scrollbar {
  width: 8px;
}

.analysis-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.analysis-content::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.4);
  border-radius: 4px;
  transition: background 0.3s ease;
}

.analysis-content::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.6);
}

/* 动画 */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>

