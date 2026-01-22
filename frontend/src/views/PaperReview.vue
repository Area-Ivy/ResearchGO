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

    <!-- Paper Selection Dialog -->
    <div v-if="showPaperList" class="modal-overlay" @click="showPaperList = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Select Paper</h2>
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
                  Size: {{ formatSize(paper.size) }} | 
                  Uploaded: {{ formatDate(paper.last_modified) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="content-wrapper">
      <!-- Left: PDF Viewer -->
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

      <!-- Right: Feature Panel -->
      <div class="feature-panel">
        <!-- Feature Tabs -->
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

        <!-- Feature Content -->
        <div class="feature-content">
          <!-- Mind Map -->
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
                <p>AI is analyzing the paper and generating the mind map...</p>
                <p style="font-size: 12px; color: var(--text-tertiary); margin-top: 8px;">Estimated time: 10-30 seconds</p>
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
                <h3 style="color: var(--text-primary); margin: 16px 0 8px;">Ready to Generate</h3>
                <p style="color: var(--text-secondary);">Click "Generate Map" to start AI analysis</p>
              </div>
            </div>
          </div>

          <!-- Analysis -->
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
                <p>AI is deeply analyzing the paper...</p>
                <p style="font-size: 12px; color: var(--text-tertiary); margin-top: 8px;">Estimated time: 20-60 seconds</p>
              </div>
              <div v-else-if="analysisGenerated && analysisData" class="analysis-content">
                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                    <h4>Paper Title</h4>
                  </div>
                  <p class="section-content highlight-title">{{ analysisData.title }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M4 7h16M4 12h16M4 17h10"></path>
                    </svg>
                    <h4>Abstract</h4>
                  </div>
                  <p class="section-content">{{ analysisData.abstract }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <path d="M12 16v-4M12 8h.01"></path>
                    </svg>
                    <h4>Research Background</h4>
                  </div>
                  <p class="section-content">{{ analysisData.research_background }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01"></path>
                    </svg>
                    <h4>Research Problem</h4>
                  </div>
                  <p class="section-content">{{ analysisData.research_problem }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                      <path d="M2 17l10 5 10-5M2 12l10 5 10-5"></path>
                    </svg>
                    <h4>Methodology</h4>
                  </div>
                  <p class="section-content">{{ analysisData.methodology }}</p>
                </div>

                <div class="analysis-section highlight">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M3 3v18h18"></path>
                      <path d="m19 9-5 5-4-4-3 3"></path>
                    </svg>
                    <h4>Key Findings</h4>
                  </div>
                  <p class="section-content">{{ analysisData.key_findings }}</p>
                </div>

                <div class="analysis-section highlight">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path>
                    </svg>
                    <h4>Innovations</h4>
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
                    <h4>Limitations</h4>
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
                    <h4>Future Work</h4>
                  </div>
                  <p class="section-content">{{ analysisData.future_work }}</p>
                </div>

                <div class="analysis-section">
                  <div class="section-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="9 11 12 14 22 4"></polyline>
                      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                    </svg>
                    <h4>Conclusion</h4>
                  </div>
                  <p class="section-content">{{ analysisData.conclusion }}</p>
                </div>
              </div>
              <div v-else class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.3;">
                  <path d="M3 3v18h18"></path>
                  <path d="m19 9-5 5-4-4-3 3"></path>
                </svg>
                <h3 style="color: var(--text-primary); margin: 16px 0 8px;">Ready to Analyze</h3>
                <p style="color: var(--text-secondary);">{{ selectedPaper ? 'Click "Generate Analysis" to start AI analysis' : 'Please select a paper first' }}</p>
              </div>
            </div>
          </div>

          <!-- Citation Graph -->
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
                <h3>Coming Soon</h3>
                <p>Citation relationship visualization feature is under development...</p>
              </div>
            </div>
          </div>

          <!-- AI Assistant -->
          <div v-show="activeTab === 'assistant'" class="feature-view">
            <div class="feature-header">
              <div class="feature-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  <line x1="9" y1="9" x2="15" y2="9"></line>
                  <line x1="9" y1="13" x2="12" y2="13"></line>
                </svg>
                <h3>AI Assistant</h3>
                <span class="badge badge-primary" v-if="chatMessages.length > 0">{{ chatMessages.length }} messages</span>
              </div>
              <div class="feature-controls" v-if="chatMessages.length > 0">
                <button 
                  @click="clearChat" 
                  class="btn btn-secondary btn-sm"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                  <span>Clear</span>
                </button>
              </div>
            </div>
            <div class="feature-body chat-container-wrapper">
              <!-- Empty State -->
              <div v-if="!selectedPaper" class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.3;">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  <circle cx="9" cy="10" r="1"></circle>
                  <circle cx="15" cy="10" r="1"></circle>
                  <path d="M9 14c1.5 1 3.5 1 5 0"></path>
                </svg>
                <h3 style="color: var(--text-primary); margin: 16px 0 8px;">Ready to Start</h3>
                <p style="color: var(--text-secondary);">Please select a paper first, then you can ask the AI assistant any questions about it</p>
              </div>

              <!-- Chat Interface -->
              <div v-else class="chat-wrapper">
                <!-- Message List -->
                <div ref="chatContainer" class="chat-messages">
                  <!-- Welcome Message -->
                  <div v-if="chatMessages.length === 0" class="welcome-message">
                    <div class="welcome-icon">
                      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        <circle cx="9" cy="10" r="1" fill="currentColor"></circle>
                        <circle cx="15" cy="10" r="1" fill="currentColor"></circle>
                        <path d="M9 14c1.5 1 3.5 1 5 0"></path>
                      </svg>
                    </div>
                    <h4>Hello! I'm your AI Assistant</h4>
                    <p>I can help you understand this paper. You can ask me:</p>
                    <div class="example-questions">
                      <button @click="currentQuestion = 'What is the main research content of this paper?'" class="example-question">
                        📄 What is the main research content of this paper?
                      </button>
                      <button @click="currentQuestion = 'What are the innovations of this paper?'" class="example-question">
                        💡 What are the innovations of this paper?
                      </button>
                      <button @click="currentQuestion = 'What research methods does this paper use?'" class="example-question">
                        🔬 What research methods does this paper use?
                      </button>
                      <button @click="currentQuestion = 'What are the conclusions of this paper?'" class="example-question">
                        ✅ What are the conclusions of this paper?
                      </button>
                    </div>
                  </div>

                  <!-- Message Bubbles -->
                  <div 
                    v-for="(message, index) in chatMessages" 
                    :key="index"
                    :class="['message-bubble', message.role]"
                  >
                    <div class="message-avatar">
                      <svg v-if="message.role === 'user'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                      </svg>
                      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                        <path d="M2 17l10 5 10-5M2 12l10 5 10-5"></path>
                      </svg>
                    </div>
                    <div class="message-content-wrapper">
                      <div class="message-header">
                        <span class="message-role">{{ message.role === 'user' ? 'You' : 'AI Assistant' }}</span>
                        <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                      </div>
                      <div :class="['message-content', { 'error-message': message.isError }]" v-html="message.content"></div>
                      <!-- References -->
                      <div v-if="message.references && message.references.length > 0" class="message-references">
                        <div class="references-header">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                          </svg>
                          <span>References ({{ message.references.length }})</span>
                        </div>
                        <div class="references-list">
                          <div 
                            v-for="(ref, refIndex) in message.references" 
                            :key="refIndex"
                            class="reference-item"
                          >
                            <div class="reference-badge">{{ refIndex + 1 }}</div>
                            <div class="reference-info">
                              <div class="reference-meta">
                                <span class="reference-pages">Pages: {{ ref.page_range }}</span>
                                <span class="reference-score">Relevance: {{ Math.round(ref.relevance_score * 100) }}%</span>
                              </div>
                              <div class="reference-content">{{ ref.content.substring(0, 150) }}...</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Typing Indicator -->
                  <div v-if="isAsking" class="message-bubble assistant typing-indicator">
                    <div class="message-avatar">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                        <path d="M2 17l10 5 10-5M2 12l10 5 10-5"></path>
                      </svg>
                    </div>
                    <div class="message-content-wrapper">
                      <div class="message-content">
                        <div class="typing-dots">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Input Box -->
                <div class="chat-input-container">
                  <div class="chat-input-wrapper">
                    <textarea
                      v-model="currentQuestion"
                      @keydown.enter.exact.prevent="sendQuestion"
                      @keydown.enter.shift.exact="currentQuestion += '\n'"
                      placeholder="Type your question... (Shift+Enter for new line)"
                      class="chat-input"
                      rows="1"
                      :disabled="isAsking"
                    ></textarea>
                    <button 
                      @click="sendQuestion"
                      :disabled="!currentQuestion.trim() || isAsking"
                      class="send-button"
                    >
                      <svg v-if="!isAsking" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                      </svg>
                      <div v-else class="send-spinner"></div>
                    </button>
                  </div>
                  <div class="input-hint">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <path d="M12 16v-4M12 8h.01"></path>
                    </svg>
                    <span>Press Enter to send, Shift+Enter for new line</span>
                  </div>
                </div>
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
import { listPapers, downloadPaper, paperQA } from '../api/papers'
import { generateMindmap as generateMindmapAPI } from '../api/mindmap'
import { generateAnalysis as generateAnalysisAPI } from '../api/analysis'
import jsMind from 'jsmind'
import 'jsmind/style/jsmind.css'
import { marked } from 'marked'
import katex from 'katex'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'
import 'katex/dist/katex.min.css'
import { API_BASE_URL } from '../config'

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

    // AI 助手相关
    const chatMessages = ref([])
    const currentQuestion = ref('')
    const isAsking = ref(false)
    const chatContainer = ref(null)

    // 加载论文列表
    const loadPapers = async () => {
      loading.value = true
      try {
        const response = await listPapers()
        papers.value = response.papers || []
      } catch (error) {
        console.error('Failed to load papers:', error)
        alert('Failed to load papers list')
      } finally {
        loading.value = false
      }
    }

    // Select paper
    const selectPaper = (paper) => {
      selectedPaper.value = paper
      showPaperList.value = false
      // Use paper storage service view endpoint
      const token = localStorage.getItem('token')
      pdfUrl.value = `http://localhost:8003/api/papers/view/${paper.object_name}?token=${token}`
    }

    // 重置选择
    const resetSelection = () => {
      selectedPaper.value = null
      pdfUrl.value = ''
      mindmapGenerated.value = false
      mindmapData.value = null
      analysisGenerated.value = false
      analysisData.value = null
      chatMessages.value = []
      currentQuestion.value = ''
      
      // Clear mindmap
      if (jsMindInstance) {
        jsMindInstance = null
      }
      if (mindmapContainer.value) {
        mindmapContainer.value.innerHTML = ''
      }
    }

    // Generate mindmap
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
            throw new Error('Mindmap data returned from backend is empty')
          }
          console.log('Received mindmap data:', result.mindmap_data)
          mindmapData.value = result.mindmap_data
          await renderMindmap(result.mindmap_data)
          mindmapGenerated.value = true
        } else {
          throw new Error(result.message || 'Failed to generate mindmap')
        }
      } catch (error) {
        console.error('Failed to generate mindmap:', error)
        alert('Failed to generate mindmap: ' + (error.response?.data?.detail || error.message))
      } finally {
        generatingMindmap.value = false
      }
    }

    // Regenerate mindmap
    const regenerateMindmap = async () => {
      mindmapGenerated.value = false
      mindmapData.value = null
      if (jsMindInstance) {
        markmapInstance.value.destroy()
        markmapInstance.value = null
      }
      await generateMindmap()
    }

    // Add zoom functionality (keeping scroll position)
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
        alert('Failed to render mindmap: ' + error.message)
      }
    }

    // Generate analysis
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
            throw new Error('Analysis data returned from backend is empty')
          }
          console.log('Received analysis data:', result.analysis)
          analysisData.value = result.analysis
          analysisGenerated.value = true
        } else {
          throw new Error(result.message || 'Failed to generate analysis')
        }
      } catch (error) {
        console.error('Failed to generate analysis:', error)
        alert('Failed to generate analysis: ' + (error.response?.data?.detail || error.message))
      } finally {
        generatingAnalysis.value = false
      }
    }

    // Regenerate analysis
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

    // AI Assistant - Send question with streaming
    const sendQuestion = async () => {
      if (!currentQuestion.value.trim() || !selectedPaper.value || isAsking.value) return
      
      const question = currentQuestion.value.trim()
      currentQuestion.value = ''
      
      // Add user message
      const userMessage = {
        role: 'user',
        content: question,
        timestamp: new Date().toISOString()
      }
      chatMessages.value.push(userMessage)
      
      // Scroll to bottom
      await nextTick()
      scrollToBottom()
      
      isAsking.value = true
      let assistantMessageIndex = -1
      let fullResponse = ''
      
      try {
        // Prepare chat history (only send role and content, without HTML)
        const history = chatMessages.value.slice(0, -1).map(msg => ({
          role: msg.role,
          content: typeof msg.content === 'string' ? msg.content.replace(/<[^>]*>/g, '') : msg.content
        }))
        
        // Call vector search service streaming API
        const token = localStorage.getItem('token')
        const response = await fetch('http://localhost:8004/api/vector/qa-stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            paper_id: selectedPaper.value.object_name,
            question: question,
            chat_history: history,
            top_k: 10
          })
        })
        
        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`)
        }
        
        // Read SSE stream
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let references = []
        
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
                
                // Handle different event types
                if (parsed.content) {
                  fullResponse += parsed.content
                  
                  // Create placeholder message when first content arrives
                  if (assistantMessageIndex === -1) {
                    isAsking.value = false
                    assistantMessageIndex = chatMessages.value.length
                    chatMessages.value.push({
                      role: 'assistant',
                      content: '',
                      references: [],
                      timestamp: new Date().toISOString()
                    })
                  }
                  
                  // Render LaTeX first, then markdown
                  const latexRendered = renderLatex(fullResponse)
                  chatMessages.value[assistantMessageIndex].content = marked(latexRendered)
                  
                  await nextTick()
                  scrollToBottom()
                }
                
                // Handle references
                if (parsed.references) {
                  references = parsed.references
                  if (assistantMessageIndex >= 0) {
                    chatMessages.value[assistantMessageIndex].references = references
                  }
                }
                
                // Handle errors
                if (parsed.error) {
                  throw new Error(parsed.error)
                }
                
                // Handle done signal
                if (parsed.done || parsed.response_time_ms !== undefined) {
                  console.log(`QA completed in ${parsed.response_time_ms}ms`)
                }
              } catch (e) {
                if (e instanceof SyntaxError) {
                  continue
                }
                throw e
              }
            } else if (line.startsWith('event: ')) {
              // Handle event type (references, error, done, etc.)
              const eventType = line.slice(7)
              console.log('Event type:', eventType)
            }
          }
        }
        
        isAsking.value = false
        
      } catch (error) {
        console.error('Failed to get answer:', error)
        
        isAsking.value = false
        
        // Update placeholder message with error or create new one
        if (assistantMessageIndex >= 0 && chatMessages.value[assistantMessageIndex]) {
          chatMessages.value[assistantMessageIndex].content = `<div class="error-message">
            <strong>Error:</strong> ${error.message || 'Failed to get answer'}
            <br><br>
            Please make sure the backend server is running.
          </div>`
          chatMessages.value[assistantMessageIndex].isError = true
        } else {
          chatMessages.value.push({
            role: 'assistant',
            content: `<div class="error-message">
              <strong>Error:</strong> ${error.message || 'Failed to get answer'}
              <br><br>
              Please make sure the backend server is running.
            </div>`,
            isError: true,
            timestamp: new Date().toISOString()
          })
        }
        
        await nextTick()
        scrollToBottom()
      }
    }

    // Scroll to chat bottom
    const scrollToBottom = () => {
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
    }

    // Clear chat history
    const clearChat = () => {
      chatMessages.value = []
    }

    // Format time
    const formatTime = (timestamp) => {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    // Render LaTeX with KaTeX
    const renderLatex = (text) => {
      if (!text) return text
      
      const isValidLatex = (formula) => {
        const trimmed = formula.trim()
        if (!trimmed || trimmed.length < 2) return false
        if (/^[0-9\s]+$/.test(trimmed)) return false
        return /[\\_{}\^=+\-*/()]|\\[a-zA-Z]+/.test(trimmed)
      }
      
      text = text.replace(/\\\[([\s\S]*?)\\\]/g, (match, content) => {
        return isValidLatex(content) ? `$$${content}$$` : match
      })
      text = text.replace(/\\\((.*?)\\\)/g, (match, content) => {
        return isValidLatex(content) ? `$${content}$` : match
      })
      text = text.replace(/^\s*\[([\s\S]*?)\]\s*$/gm, (match, content) => {
        return isValidLatex(content) ? `$$${content}$$` : match
      })
      
      try {
        text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
          const trimmed = formula.trim()
          if (!isValidLatex(trimmed)) return match
          try {
            const html = katex.renderToString(trimmed, {
              displayMode: true,
              throwOnError: false,
              trust: true,
              strict: false
            })
            if (html && !html.includes('katex-error')) {
              return `<div class="katex-block">${html}</div>`
            }
            return match
          } catch (err) {
            console.warn('KaTeX block error:', err.message)
            return match
          }
        })
        
        text = text.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
          const trimmed = formula.trim()
          if (!isValidLatex(trimmed)) return match
          try {
            const html = katex.renderToString(trimmed, {
              displayMode: false,
              throwOnError: false,
              trust: true,
              strict: false
            })
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
      chatMessages,
      currentQuestion,
      isAsking,
      chatContainer,
      selectPaper,
      resetSelection,
      generateMindmap,
      regenerateMindmap,
      generateAnalysis,
      regenerateAnalysis,
      sendQuestion,
      clearChat,
      formatSize,
      formatDate,
      formatTime
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

/* 聊天界面样式 */
.chat-container-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.chat-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: rgba(0, 0, 0, 0.15);
}

/* 欢迎消息 */
.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
  gap: 16px;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-primary);
  margin-bottom: 8px;
}

.welcome-message h4 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.welcome-message p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 16px 0;
}

.example-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 500px;
}

.example-question {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
  font-size: 13px;
}

.example-question:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(99, 102, 241, 0.5);
  color: var(--text-primary);
  transform: translateX(4px);
}

/* 消息气泡 */
.message-bubble {
  display: flex;
  gap: 12px;
  animation: messageSlideIn 0.3s ease;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-bubble.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.message-bubble.user .message-avatar {
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  border-color: transparent;
  color: white;
}

.message-content-wrapper {
  flex: 1;
  min-width: 0;
  max-width: 70%;
}

.message-bubble.user .message-content-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
}

.message-bubble.user .message-header {
  flex-direction: row-reverse;
}

.message-role {
  font-weight: 600;
  color: var(--text-primary);
}

.message-time {
  color: var(--text-tertiary);
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-bubble.user .message-content {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3));
  border-color: rgba(99, 102, 241, 0.5);
  white-space: pre-wrap;
}

.message-bubble.assistant .message-content {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
}

.error-message {
  background: rgba(255, 107, 157, 0.1) !important;
  border-color: var(--accent-danger) !important;
  color: var(--accent-danger) !important;
}

/* Markdown Styles */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3),
.message-content :deep(h4) {
  color: var(--text-primary);
  margin: 16px 0 12px 0;
  font-weight: 600;
  line-height: 1.4;
}

.message-content :deep(h1) { font-size: 20px; }
.message-content :deep(h2) { font-size: 18px; }
.message-content :deep(h3) { font-size: 16px; }
.message-content :deep(h4) { font-size: 15px; }

.message-content :deep(p) {
  margin: 8px 0;
  line-height: 1.7;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.message-content :deep(li) {
  margin: 6px 0;
  line-height: 1.6;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #00ff88;
}

.message-content :deep(pre) {
  background: #282c34;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
}

.message-content :deep(pre code) {
  background: none;
  padding: 0;
  color: #abb2bf;
  font-size: 13px;
}

.message-content :deep(blockquote) {
  border-left: 3px solid var(--accent-primary);
  padding-left: 16px;
  margin: 16px 0;
  color: var(--text-secondary);
  font-style: italic;
}

.message-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.message-content :deep(th),
.message-content :deep(td) {
  padding: 10px;
  border: 1px solid var(--border-primary);
  text-align: left;
}

.message-content :deep(th) {
  background: var(--bg-tertiary);
  font-weight: 600;
}

.message-content :deep(strong) {
  font-weight: 600;
  color: var(--accent-primary);
}

.message-content :deep(em) {
  font-style: italic;
  color: var(--text-secondary);
}

.message-content :deep(a) {
  color: var(--accent-primary);
  text-decoration: none;
  border-bottom: 1px solid var(--accent-primary);
  transition: all 0.2s;
}

.message-content :deep(a:hover) {
  opacity: 0.8;
}

.message-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-primary);
  margin: 16px 0;
}

/* KaTeX Math Rendering */
.message-content :deep(.katex-block) {
  margin: 0.5rem 0;
  padding: 0.5rem 1rem;
  background: rgba(102, 126, 234, 0.05);
  border-left: 3px solid rgba(102, 126, 234, 0.5);
  border-radius: 4px;
  overflow-x: auto;
}

.message-content :deep(.katex) {
  font-size: 1.05em;
}

.message-content :deep(.katex-display) {
  margin: 0;
  text-align: center;
}

.message-content :deep(.katex-html) {
  color: var(--text-primary);
}

.message-content :deep(.katex-error) {
  display: none;
}

.message-content :deep(.katex-mathml) {
  display: none;
}

/* User message markdown styles */
.message-bubble.user .message-content :deep(h1),
.message-bubble.user .message-content :deep(h2),
.message-bubble.user .message-content :deep(h3),
.message-bubble.user .message-content :deep(h4),
.message-bubble.user .message-content :deep(p),
.message-bubble.user .message-content :deep(li),
.message-bubble.user .message-content :deep(strong) {
  color: white;
}

.message-bubble.user .message-content :deep(code) {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

/* 引用参考 */
.message-references {
  margin-top: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 10px;
}

.references-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.references-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reference-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.reference-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(99, 102, 241, 0.3);
}

.reference-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.reference-info {
  flex: 1;
  min-width: 0;
}

.reference-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.reference-pages,
.reference-score {
  font-family: 'Courier New', monospace;
}

.reference-content {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 正在输入指示器 */
.typing-indicator {
  animation: none;
}

.typing-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-primary);
  animation: typingBounce 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingBounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

/* 输入框 */
.chat-input-container {
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.chat-input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.chat-input-wrapper:focus-within {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
  background: rgba(255, 255, 255, 0.05);
}

.chat-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  max-height: 120px;
  font-family: inherit;
}

.chat-input::placeholder {
  color: var(--text-tertiary);
}

.chat-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-button {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.send-button:hover:not(:disabled) {
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.5);
  transform: translateY(-2px);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.send-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.input-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.input-hint svg {
  opacity: 0.7;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.4);
  border-radius: 4px;
  transition: background 0.3s ease;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.6);
}

/* 动画 */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>

