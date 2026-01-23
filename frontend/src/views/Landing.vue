<template>
  <div class="landing">
    <!-- Dynamic Neural Background -->
    <div class="bg-neural">
      <canvas ref="neuralCanvas" class="neural-canvas"></canvas>
      <div class="gradient-overlay"></div>
    </div>

    <!-- Navigation -->
    <nav class="nav" :class="{ 'nav-scrolled': isScrolled }">
      <div class="nav-container">
        <div class="nav-brand">
          <svg class="brand-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#brandGrad)" stroke-width="2">
            <defs>
              <linearGradient id="brandGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#6366f1"/>
                <stop offset="100%" stop-color="#06b6d4"/>
              </linearGradient>
            </defs>
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
          <span class="brand-text">ResearchGO</span>
        </div>
        <div class="nav-links">
          <a href="#features">Features</a>
          <a href="#workflow">How It Works</a>
        </div>
        <div class="nav-actions">
          <router-link to="/login" class="btn-text">Sign In</router-link>
          <router-link to="/login" class="btn-primary">Get Started</router-link>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="hero">
      <!-- Floating Orbs -->
      <div class="hero-orbs">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
      </div>
      
      <!-- Orbit Decoration -->
      <div class="hero-orbit">
        <div class="orbit-ring orbit-1">
          <div class="orbit-dot"></div>
        </div>
        <div class="orbit-ring orbit-2">
          <div class="orbit-dot"></div>
        </div>
        <div class="orbit-ring orbit-3">
          <div class="orbit-dot"></div>
        </div>
      </div>
      
      <div class="hero-container">
        <div class="hero-badge">
          <span class="badge-pulse"></span>
          <span>AI-Powered Research Platform</span>
        </div>
        
        <h1 class="hero-title">
          Transform Research Papers<br>
          Into <span class="title-highlight">Actionable Knowledge</span>
        </h1>
        
        <p class="hero-desc">
          Upload papers, ask questions in natural language, and let AI build 
          your knowledge graph. Discover connections humans miss.
        </p>
        
        <div class="hero-actions">
          <router-link to="/login" class="btn-hero">
            <span>Start Free Trial</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </router-link>
          <a href="#demo" class="btn-ghost">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polygon points="10 8 16 12 10 16"/>
            </svg>
            <span>Watch Demo</span>
          </a>
        </div>
        
        <div class="hero-stats">
          <div class="stat">
            <span class="stat-value">{{ animatedStats.papers.toLocaleString() }}</span>
            <span class="stat-label">Papers Analyzed</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat">
            <span class="stat-value">{{ animatedStats.researchers.toLocaleString() }}</span>
            <span class="stat-label">Researchers</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat">
            <span class="stat-value">{{ animatedStats.hours }}h</span>
            <span class="stat-label">Saved Weekly</span>
          </div>
        </div>
      </div>
      
      <!-- Preview Window -->
      <div class="hero-preview" id="demo">
        <div class="preview-window">
          <div class="window-bar">
            <div class="window-dots">
              <span></span><span></span><span></span>
            </div>
            <div class="window-title">ResearchGO — Analysis</div>
          </div>
          <div class="window-content">
            <div class="preview-sidebar">
              <div class="sidebar-header">
                <span class="sidebar-title">Library</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
              </div>
              <div class="paper-list">
                <div class="paper-item active">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  <div class="paper-info">
                    <span class="paper-name">Attention Is All You Need</span>
                    <span class="paper-meta">Vaswani et al.</span>
                  </div>
                </div>
                <div class="paper-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  <div class="paper-info">
                    <span class="paper-name">BERT: Pre-training of Deep...</span>
                    <span class="paper-meta">Devlin et al.</span>
                  </div>
                </div>
                <div class="paper-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  <div class="paper-info">
                    <span class="paper-name">GPT-4 Technical Report</span>
                    <span class="paper-meta">OpenAI</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="preview-main">
              <div class="main-header">
                <h4>Key Insights</h4>
                <div class="status-indicator">
                  <span class="status-dot"></span>
                  <span>Analyzing</span>
                </div>
              </div>
              <div class="insights-list">
                <div class="insight-item">
                  <div class="insight-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                    </svg>
                  </div>
                  <div class="insight-content">
                    <strong>Core Innovation</strong>
                    <p>Self-attention mechanism eliminates recurrence, enabling parallel computation across sequence positions.</p>
                  </div>
                </div>
                <div class="insight-item">
                  <div class="insight-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="3"/>
                      <circle cx="19" cy="5" r="2"/>
                      <circle cx="5" cy="19" r="2"/>
                      <line x1="14" y1="10" x2="17" y2="7"/>
                      <line x1="10" y1="14" x2="7" y2="17"/>
                    </svg>
                  </div>
                  <div class="insight-content">
                    <strong>Related Works</strong>
                    <p>Found 847 citing papers. 23 share similar methodology patterns.</p>
                  </div>
                </div>
                <div class="insight-item loading">
                  <div class="insight-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                  </div>
                  <div class="insight-content">
                    <strong>Research Gaps</strong>
                    <p>Identifying unexplored directions<span class="typing-cursor"></span></p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="features-section" id="features">
      <div class="section-container">
        <div class="section-header">
          <span class="section-label">Features</span>
          <h2 class="section-title">Everything You Need for Modern Research</h2>
          <p class="section-desc">Six powerful capabilities that transform how you interact with scientific literature.</p>
        </div>
        
        <div class="features-grid">
          <div class="feature-card" v-for="(feature, i) in features" :key="i">
            <div class="card-glow"></div>
            <div class="card-shine"></div>
            <div class="feature-icon" :style="{ '--accent': feature.color }">
              <div v-html="feature.icon"></div>
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Workflow -->
    <section class="workflow-section" id="workflow">
      <div class="section-container">
        <div class="section-header">
          <span class="section-label">Workflow</span>
          <h2 class="section-title">From Papers to Insights in Minutes</h2>
          <p class="section-desc">A streamlined process that accelerates every stage of your research.</p>
        </div>
        
        <div class="workflow-steps">
          <div class="workflow-line"></div>
          <div class="step" v-for="(step, i) in workflowSteps" :key="i">
            <div class="step-number">{{ String(i + 1).padStart(2, '0') }}</div>
            <div class="step-content">
              <div class="step-header">
                <h3 class="step-title">{{ step.title }}</h3>
                <p class="step-desc">{{ step.desc }}</p>
              </div>
              <ul class="step-list">
                <li v-for="(item, j) in step.items" :key="j">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  {{ item }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta-section">
      <div class="cta-bg">
        <div class="cta-orb cta-orb-1"></div>
        <div class="cta-orb cta-orb-2"></div>
        <div class="cta-orb cta-orb-3"></div>
        <div class="cta-grid"></div>
      </div>
      <div class="cta-content">
        <h2 class="cta-title">Ready to Accelerate Your Research?</h2>
        <p class="cta-desc">Join thousands of researchers who've transformed their workflow.</p>
        <router-link to="/login" class="btn-cta">
          <span>Get Started Free</span>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
          <div class="btn-shine"></div>
        </router-link>
        <span class="cta-note">No credit card required</span>
      </div>
    </section>

    <!-- Powered By -->
    <section class="powered-section">
      <div class="powered-label">Powered By</div>
      <div class="powered-row">
        <!-- Vue.js -->
        <div class="powered-item">
          <svg viewBox="0 0 128 128" width="24" height="24"><path fill="#42b883" d="M78.8,10L64,35.4L49.2,10H0l64,110l64-110C128,10,78.8,10,78.8,10z"/><path fill="#35495e" d="M78.8,10L64,35.4L49.2,10H25.6L64,76l38.4-66H78.8z"/></svg>
          <span>Vue</span>
        </div>
        <!-- FastAPI -->
        <div class="powered-item">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="#009688"><path d="M12 0C5.375 0 0 5.375 0 12c0 6.627 5.375 12 12 12 6.626 0 12-5.373 12-12 0-6.625-5.373-12-12-12zm-.624 21.62v-7.528H7.19L13.203 2.38v7.528h4.029L11.376 21.62z"/></svg>
          <span>FastAPI</span>
        </div>
        <!-- OpenAI -->
        <div class="powered-item">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08-4.778 2.758a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/></svg>
          <span>OpenAI</span>
        </div>
        <!-- OpenAlex -->
        <div class="powered-item">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
          <span>OpenAlex</span>
        </div>
        <!-- MySQL -->
        <div class="powered-item">
          <svg viewBox="0 0 128 128" width="24" height="24"><path fill="#00618A" d="M116.948 97.807c-6.863-.187-12.104.452-16.585 2.341-1.273.537-3.305.552-3.513 2.147.7.733.807 1.83 1.355 2.731 1.063 1.749 2.86 4.088 4.489 5.319 1.774 1.338 3.578 2.769 5.517 3.916 3.459 2.043 7.331 3.209 10.661 5.251 1.956 1.203 3.889 2.735 5.834 4.104.963.68 1.611 1.74 2.856 2.128v-.241c-.656-.836-1.052-1.995-1.754-2.794-1.095-1.118-2.3-2.108-3.548-3.065-3.463-2.642-11.002-6.21-12.396-10.378l-.242-.241c2.398-.282 5.224-1.175 7.514-1.904 3.783-.96 7.175-.744 11.071-1.707.925-.241 1.853-.496 2.78-.744v-1.139c-1.039-1.066-1.772-2.482-2.914-3.459-2.995-2.573-6.313-5.003-9.69-7.125-1.894-1.191-4.39-1.975-6.42-3.018-1.168-.609-1.906-1.065-2.984-1.782-.648-.408-1.085-1.034-1.844-1.334v.263h.011z"/><path fill="#00618A" d="M109.456 83.094c-.024-.012-.039-.027-.051-.051l-.014.007c-.137.213-.156.496-.263.744-.119 1.012-.193 2.024-.337 3.011-.481 2.929-1.082 5.743-1.916 8.377-.413 1.299-.882 2.592-1.337 3.878-.249.708-1.169 2.88-1.168 3.529 0 .649 1.074 1.692 1.602 2.236.925.953 2.443 2.079 3.507 2.834 2.13 1.513 4.548 2.898 6.882 4.137 1.262.67 2.652 1.112 3.947 1.71.577.267 1.183.758 1.843.909l.031-.014c-.375-.594-.498-1.402-.819-2.054-.536-1.088-1.177-2.147-1.795-3.188-1.294-2.174-2.761-4.128-4.188-6.189-.728-1.052-1.476-2.086-2.086-3.231-.318-.596-.485-1.485-.918-1.91-.345.36-.851.741-1.122 1.168-.534.842-.629 1.919-.906 2.977-.477-.142-.809-.713-1.087-1.077-.716-.939-1.416-2.186-1.948-3.268-1.341-2.728-2.531-5.736-3.574-8.717-.386-1.103-.622-2.188-.944-3.268-.129-.434-.099-1.084-.403-1.348l.007-.045z"/><path fill="#105E86" d="M2.497 72.871c3.023 1.675 6.574 2.462 10.14 3.701 1.952.678 4.038 1.094 5.925 1.943 1.004.451 1.983.968 2.979 1.468l1.418.751v-.061c-.627-.673-.824-1.635-1.354-2.403-1.055-1.529-2.24-2.949-3.455-4.352-.991-1.143-1.928-2.348-2.933-3.481-.524-.592-.87-1.474-1.544-1.891-.623.911-1.5 1.683-2.067 2.66-1.135 1.951-2.129 4.157-2.995 6.346-.289.733-1.135 2.987-.706 3.706l.023.021z"/><path fill="#105E86" d="M58.01 2.452c-2.052.053-3.578.632-5.08 1.343-3.971 1.893-7.193 4.66-9.972 7.942-2.945 3.478-5.212 7.327-7.454 11.437-.928 1.699-1.661 3.545-2.531 5.35-.403.839-.604 1.702-1.026 2.496-.865 1.628-1.848 3.263-2.635 4.962-1.511 3.265-2.79 6.722-4.052 10.147-1.252 3.395-2.48 6.809-3.496 10.303-1.035 3.556-2.195 7.057-3.022 10.697-.462 2.034-.787 4.113-1.266 6.124-.488 2.052-.979 4.112-1.376 6.199-.202 1.06-.257 2.14-.46 3.19-.455 2.349-1.057 4.663-1.386 7.043-.209 1.512.005 3.006-.224 4.479-.178 1.145-.767 2.201-.84 3.377-.099 1.602.166 3.159.153 4.751-.006.666-.241 1.326-.193 1.98.126 1.731.551 3.42.706 5.157.103 1.148.04 2.312.205 3.445.17 1.168.533 2.293.734 3.458.11.634.091 1.284.251 1.904.346 1.34.846 2.632 1.253 3.954.267.868.433 1.774.771 2.604.401.984.958 1.899 1.398 2.862.346.757.608 1.54 1.006 2.272.431.794.993 1.511 1.433 2.302.476.856.863 1.766 1.4 2.575.496.746 1.063 1.443 1.573 2.18.498.72.907 1.509 1.466 2.175.63.752 1.349 1.425 1.998 2.16.552.626 1.024 1.327 1.626 1.901.716.684 1.518 1.279 2.254 1.942.694.625 1.305 1.357 2.047 1.918.715.542 1.493.996 2.223 1.517.641.458 1.229.989 1.89 1.414.774.498 1.611.899 2.395 1.38.704.433 1.367.929 2.087 1.327.685.379 1.415.677 2.106 1.046.795.424 1.56.907 2.377 1.288.769.358 1.58.627 2.36.963.943.406 1.862.883 2.831 1.229.806.287 1.65.479 2.468.729.995.305 1.972.683 2.988.911 1.117.251 2.262.373 3.387.591 1.094.212 2.177.525 3.285.657 1.106.132 2.224.132 3.336.246 1.076.11 2.143.348 3.224.389 1.092.041 2.185.02 3.278.035 1.214.017 2.427.085 3.64.05 1.167-.034 2.329-.175 3.494-.259 1.201-.087 2.406-.12 3.601-.276 1.219-.159 2.418-.445 3.628-.67 1.222-.227 2.449-.422 3.66-.711 1.233-.295 2.444-.672 3.666-1.012 1.181-.329 2.372-.621 3.536-1.013 1.224-.413 2.415-.917 3.62-1.387 1.148-.448 2.313-.855 3.436-1.366 1.161-.528 2.28-1.146 3.42-1.714 1.118-.558 2.253-1.084 3.343-1.698 1.063-.599 2.075-1.286 3.116-1.922 1.012-.619 2.039-1.213 3.013-1.889.962-.668 1.872-1.413 2.812-2.112 1.016-.755 2.056-1.477 3.031-2.286.926-.769 1.791-1.608 2.691-2.41.929-.827 1.876-1.633 2.76-2.511.871-.865 1.681-1.791 2.524-2.686.881-.936 1.788-1.848 2.612-2.838.751-.903 1.419-1.875 2.137-2.805.837-1.085 1.71-2.143 2.488-3.271.74-1.074 1.39-2.212 2.089-3.313.672-1.059 1.378-2.096 1.991-3.19.596-1.064 1.1-2.179 1.66-3.263.574-1.112 1.182-2.206 1.699-3.347.5-1.103.908-2.25 1.37-3.371.448-1.088.932-2.161 1.322-3.273.367-1.044.648-2.122.979-3.178.351-1.122.741-2.233 1.032-3.374.271-1.063.443-2.153.686-3.223.272-1.198.6-2.384.795-3.598.179-1.11.251-2.24.394-3.357.159-1.24.363-2.473.457-3.721.083-1.095.068-2.199.129-3.296.065-1.168.184-2.334.177-3.503-.006-1.072-.123-2.141-.169-3.212-.05-1.156-.045-2.315-.145-3.468-.096-1.1-.285-2.191-.413-3.288-.13-1.118-.21-2.243-.39-3.354-.187-1.157-.469-2.299-.69-3.45-.196-1.019-.333-2.053-.572-3.062-.247-1.042-.57-2.066-.854-3.1-.282-1.024-.521-2.061-.845-3.072-.327-1.021-.729-2.018-1.086-3.028-.329-.93-.609-1.88-.98-2.794-.382-.944-.842-1.858-1.256-2.79-.397-.894-.761-1.803-1.199-2.677-.456-.91-.992-1.779-1.474-2.676-.453-.843-.868-1.708-1.361-2.526-.523-.867-1.113-1.694-1.661-2.546-.502-.781-.967-1.585-1.506-2.339-.582-.815-1.221-1.588-1.824-2.388-.526-.699-1.014-1.427-1.574-2.097-.641-.767-1.338-1.489-2.002-2.238-.563-.635-1.088-1.303-1.684-1.906-.672-.68-1.399-1.307-2.091-1.969-.578-.553-1.115-1.147-1.721-1.668-.702-.604-1.455-1.15-2.176-1.733-.604-.488-1.177-1.01-1.803-1.471-.705-.52-1.448-.991-2.167-1.492-.593-.413-1.164-.857-1.777-1.241-.743-.465-1.522-.875-2.279-1.32-.592-.349-1.167-.729-1.776-1.047-.78-.407-1.593-.754-2.383-1.144-.577-.285-1.133-.607-1.725-.861-.839-.36-1.706-.661-2.557-.997-.562-.222-1.108-.482-1.681-.676-.869-.294-1.76-.529-2.64-.798-.534-.163-1.058-.359-1.601-.492-.889-.219-1.793-.381-2.688-.576-.53-.116-1.051-.27-1.587-.358-.925-.152-1.86-.249-2.788-.379-.463-.065-.921-.179-1.388-.224-1.094-.104-2.194-.165-3.291-.237-.385-.025-.765-.095-1.151-.099-1.028-.01-2.056.033-3.084.042-.414.003-.828-.03-1.241-.01-1.085.054-2.167.157-3.25.241-.434.034-.869.039-1.302.094-1.038.133-2.071.308-3.104.48-.398.066-.798.102-1.193.191-1.03.231-2.051.498-3.075.759-.366.093-.737.166-1.1.277-.957.291-1.905.613-2.855.933-.368.124-.74.227-1.104.366-.916.35-1.821.733-2.729 1.108-.382.158-.771.294-1.148.468-.852.394-1.692.816-2.534 1.233-.397.196-.803.37-1.193.584-.818.449-1.62.929-2.428 1.398-.4.232-.812.441-1.201.691-.768.493-1.516 1.016-2.273 1.527-.387.261-.787.5-1.162.779-.729.544-1.436 1.117-2.152 1.68-.359.282-.731.544-1.078.844-.695.601-1.368 1.228-2.049 1.846-.335.304-.683.592-1.004.911-.655.651-1.287 1.324-1.928 1.989-.315.327-.642.641-.944.981-.616.694-1.21 1.408-1.813 2.114-.295.346-.601.683-.884 1.04-.569.719-1.117 1.455-1.674 2.184-.273.357-.559.704-.82 1.07-.521.731-1.024 1.475-1.533 2.215-.25.363-.511.717-.749 1.089-.474.74-.931 1.492-1.393 2.241-.228.369-.467.73-.684 1.106-.434.752-.852 1.513-1.275 2.271-.207.371-.425.736-.621 1.114-.392.755-.77 1.517-1.152 2.278-.187.373-.385.74-.561 1.119-.354.762-.694 1.53-1.039 2.297-.167.372-.345.738-.502 1.115-.314.756-.614 1.518-.919 2.278-.146.364-.303.724-.439 1.093-.272.737-.531 1.48-.793 2.222-.124.352-.259.699-.374 1.055-.23.714-.446 1.433-.666 2.152-.102.334-.215.665-.309 1.002-.186.673-.359 1.35-.536 2.027-.08.304-.17.604-.244.911-.148.618-.282 1.24-.421 1.861-.062.275-.133.548-.19.824-.114.557-.216 1.118-.321 1.677-.047.248-.102.494-.145.743-.085.498-.16.998-.238 1.497-.035.221-.077.44-.108.663-.063.449-.116.9-.172 1.35-.024.189-.053.377-.075.566-.044.387-.081.774-.12 1.162-.016.163-.036.325-.051.489-.03.339-.055.679-.081 1.018-.011.145-.025.289-.035.434-.022.334-.039.669-.058 1.003-.008.147-.018.294-.025.441-.017.395-.029.791-.045 1.186l-.017.497c-.017.614-.029 1.229-.05 1.843l-.008.195 2.476.014c1.455.008 2.909.031 4.364.022 1.448-.009 2.896-.044 4.344-.066 1.465-.022 2.929-.043 4.394-.053l1.321-.009.012-1.263c.01-1.116-.005-2.231.009-3.347.014-1.124.057-2.247.089-3.371.032-1.142.061-2.285.109-3.426.044-1.045.104-2.089.175-3.133.07-1.026.165-2.051.261-3.076.089-.953.186-1.906.298-2.856.112-.949.237-1.896.378-2.842.142-.952.299-1.901.47-2.848.17-.943.355-1.884.559-2.821.208-.957.435-1.908.681-2.858.246-.948.511-1.892.793-2.831.29-.964.594-1.922.924-2.876.333-.963.685-1.92 1.066-2.868.388-.966.793-1.927 1.23-2.876.451-.98.929-1.949 1.436-2.906.514-.972 1.052-1.932 1.624-2.878.575-.951 1.173-1.889 1.809-2.806.652-.94 1.333-1.862 2.056-2.756.74-.914 1.516-1.798 2.335-2.648.847-.878 1.731-1.722 2.665-2.521.968-.829 1.981-1.609 3.043-2.332 1.098-.748 2.245-1.434 3.44-2.053 1.222-.632 2.493-1.188 3.806-1.674 1.323-.49 2.69-.9 4.088-1.23 1.377-.326 2.789-.57 4.218-.737 1.349-.158 2.714-.249 4.086-.267z"/></svg>
          <span>MySQL</span>
        </div>
        <!-- Redis -->
        <div class="powered-item">
          <svg viewBox="0 0 128 128" width="24" height="24"><path fill="#A41E11" d="M121.8 93.1c-6.7 3.5-41.4 17.7-48.8 21.6-7.4 3.9-11.5 3.8-17.3 1S13 98.1 6.3 94.9c-3.3-1.6-5-2.9-5-4.2V78.5s48-10.5 55.8-13.2c7.8-2.8 10.4-2.9 17-.5s46.1 9.5 52.6 11.9v12.5c0 1.3-1.5 2.7-4.9 3.9z"/><path fill="#D82C20" d="M121.8 80.5C115.1 84 80.4 98.2 73 102.1c-7.4 3.9-11.5 3.8-17.3 1-5.8-2.8-42.7-17.7-49.4-20.9-6.6-3.2-6.9-5.4-.1-8 6.8-2.5 45-17.6 52.8-20.3 7.8-2.8 10.4-2.9 17-.5 6.7 2.4 41.9 16.3 48.6 18.9 6.8 2.6 6.9 4.9.2 8.2z"/><path fill="#A41E11" d="M121.8 72.5c-6.7 3.5-41.4 17.7-48.8 21.6-7.4 3.9-11.5 3.8-17.3 1S13 77.4 6.3 74.3c-3.3-1.6-5-2.9-5-4.2V57.9s48-10.5 55.8-13.2c7.8-2.8 10.4-2.9 17-.5s46.1 9.5 52.6 11.9v12.5c0 1.3-1.5 2.7-4.9 3.9z"/><path fill="#D82C20" d="M121.8 59.8c-6.7 3.5-41.4 17.7-48.8 21.6-7.4 3.9-11.5 3.8-17.3 1C49.9 79.6 13 64.8 6.3 61.6c-6.6-3.1-6.9-5.4-.1-8 6.8-2.5 45-17.6 52.8-20.3 7.8-2.8 10.4-2.9 17-.5 6.7 2.4 41.9 16.3 48.6 18.9 6.8 2.6 6.9 5 .2 8.1z"/><path fill="#A41E11" d="M121.8 51c-6.7 3.5-41.4 17.7-48.8 21.6-7.4 3.9-11.5 3.8-17.3 1S13 55.9 6.3 52.7c-3.3-1.6-5-2.9-5-4.2V36.3s48-10.5 55.8-13.2c7.8-2.8 10.4-2.9 17-.5s46.1 9.5 52.6 11.9v12.5c0 1.4-1.5 2.7-4.9 4z"/><path fill="#D82C20" d="M121.8 38.3c-6.7 3.5-41.4 17.7-48.8 21.6-7.4 3.9-11.5 3.8-17.3 1S13 43.1 6.3 40c-6.6-3.2-6.9-5.4-.1-8 6.8-2.5 45-17.6 52.8-20.3 7.8-2.8 10.4-2.9 17-.5 6.7 2.4 41.9 16.3 48.6 18.9 6.8 2.5 6.9 4.9.2 8.2z"/><path fill="#fff" d="M80.4 26.1l-10.8 1.2-2.5 5.8-3.9-6.5-12.5-1.1 9.3-3.4-2.8-5.2 8.8 3.4 8.2-2.7-2.2 5.4zM66.5 54.5l-20.3-8.4 29.1-4.4z"/><ellipse fill="#fff" cx="38.4" cy="35.4" rx="15.5" ry="6"/><path fill="#7A0C00" d="M93.3 27.7l17.2 6.8-17.2 6.8z"/><path fill="#AD2115" d="M74.3 35.3l19-7.6v14.5z"/></svg>
          <span>Redis</span>
        </div>
        <!-- RabbitMQ -->
        <div class="powered-item">
          <svg viewBox="0 0 128 128" width="24" height="24"><path fill="#F60" d="M117.6 95.5H10.4C4.6 95.5 0 90.8 0 85.1V42.9c0-5.8 4.7-10.4 10.4-10.4h107.2c5.8 0 10.4 4.7 10.4 10.4v42.2c0 5.7-4.7 10.4-10.4 10.4z"/><path fill="#fff" d="M89.7 77.8H75.5c-1.5 0-2.6-1.2-2.6-2.6V56.8c0-1.5 1.2-2.6 2.6-2.6h14.2c1.5 0 2.6 1.2 2.6 2.6v18.4c0 1.4-1.2 2.6-2.6 2.6zm-34.2 0H41.3c-1.5 0-2.6-1.2-2.6-2.6V56.8c0-1.5 1.2-2.6 2.6-2.6h14.2c1.5 0 2.6 1.2 2.6 2.6v18.4c0 1.4-1.1 2.6-2.6 2.6z"/></svg>
          <span>RabbitMQ</span>
        </div>
        <!-- MinIO -->
        <div class="powered-item">
          <svg viewBox="0 0 128 128" width="24" height="24"><path fill="#C72C48" d="M64 0C28.7 0 0 28.7 0 64s28.7 64 64 64 64-28.7 64-64S99.3 0 64 0zm24.8 96H39.2c-2.2 0-4-1.8-4-4V36c0-2.2 1.8-4 4-4h49.6c2.2 0 4 1.8 4 4v56c0 2.2-1.8 4-4 4z"/><path fill="#fff" d="M52 52h8v24h-8zM68 52h8v24h-8z"/></svg>
          <span>MinIO</span>
        </div>
        <!-- Milvus -->
        <div class="powered-item">
          <svg viewBox="0 0 128 128" width="24" height="24"><path fill="#00A1EA" d="M64 8L8 40v48l56 32 56-32V40L64 8zm0 96L24 72V56l40 23 40-23v16L64 104z"/><path fill="#00D4FF" d="M64 8v47l40 23V40L64 8z"/><path fill="#0085CA" d="M64 8v47L24 32V40l40-32z"/></svg>
          <span>Milvus</span>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-container">
        <div class="footer-brand">
          <div class="footer-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            <span>ResearchGO</span>
          </div>
          <p class="footer-tagline">Accelerating scientific discovery.</p>
        </div>
        <div class="footer-links">
          <div class="link-col">
            <span class="col-title">Product</span>
            <a href="#">Features</a>
            <a href="#">Pricing</a>
            <a href="#">Changelog</a>
          </div>
          <div class="link-col">
            <span class="col-title">Resources</span>
            <a href="#">Documentation</a>
            <a href="#">API</a>
            <a href="#">Blog</a>
          </div>
          <div class="link-col">
            <span class="col-title">Company</span>
            <a href="#">About</a>
            <a href="#">Contact</a>
            <a href="#">Careers</a>
          </div>
          <div class="link-col">
            <span class="col-title">Legal</span>
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <span>© 2026 ResearchGO. All rights reserved.</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'

const isScrolled = ref(false)
const neuralCanvas = ref(null)

const animatedStats = reactive({
  papers: 0,
  researchers: 0,
  hours: 0
})

const features = ref([
  {
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>`,
    title: 'Semantic Search',
    desc: 'Search by meaning, not just keywords. Find relevant papers even when terminology differs.',
    color: '#6366f1'
  },
  {
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
    title: 'Paper Chat',
    desc: 'Ask questions about any paper and get precise answers with inline citations.',
    color: '#8b5cf6'
  },
  {
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="3"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><line x1="14" y1="10" x2="17" y2="7"/><line x1="10" y1="14" x2="7" y2="17"/></svg>`,
    title: 'Knowledge Graph',
    desc: 'Visualize relationships between papers, concepts, and authors at a glance.',
    color: '#06b6d4'
  },
  {
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>`,
    title: 'Mind Mapping',
    desc: 'Auto-generate hierarchical mind maps from papers or research topics.',
    color: '#10b981'
  },
  {
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>`,
    title: 'Smart Summary',
    desc: 'Get structured summaries with key findings, methods, and contributions.',
    color: '#f59e0b'
  },
  {
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
    title: 'Paper Library',
    desc: 'Organize, tag, and manage your entire research collection in one place.',
    color: '#ec4899'
  }
])

const workflowSteps = ref([
  {
    title: 'Import',
    desc: 'Add papers from anywhere',
    items: ['Drag & drop PDFs', 'Paste DOI or URL', 'Import from arXiv, PubMed, etc.']
  },
  {
    title: 'Analyze',
    desc: 'AI extracts insights automatically',
    items: ['Key findings & contributions', 'Methodology breakdown', 'Citation network analysis']
  },
  {
    title: 'Explore',
    desc: 'Navigate your knowledge visually',
    items: ['Interactive knowledge graphs', 'Concept clustering', 'Research gap identification']
  },
  {
    title: 'Export',
    desc: 'Output in any format you need',
    items: ['Literature review drafts', 'BibTeX citations', 'Mind map exports']
  }
])

let animationFrame = null

const initNeuralAnimation = () => {
  const canvas = neuralCanvas.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const particles = []
  const particleCount = 80
  
  const resize = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  
  resize()
  window.addEventListener('resize', resize)
  
  // Create particles
  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      radius: Math.random() * 2 + 1
    })
  }
  
  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // Update and draw particles
    particles.forEach((p, i) => {
      p.x += p.vx
      p.y += p.vy
      
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1
      
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(99, 102, 241, 0.5)'
      ctx.fill()
      
      // Draw connections
      particles.forEach((p2, j) => {
        if (i === j) return
        const dx = p.x - p2.x
        const dy = p.y - p2.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        
        if (dist < 150) {
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.strokeStyle = `rgba(99, 102, 241, ${0.15 * (1 - dist / 150)})`
          ctx.stroke()
        }
      })
    })
    
    animationFrame = requestAnimationFrame(animate)
  }
  
  animate()
}

const animateStats = () => {
  const targets = { papers: 52847, researchers: 8420, hours: 23 }
  const duration = 2000
  const start = performance.now()
  
  const step = (ts) => {
    const progress = Math.min((ts - start) / duration, 1)
    const ease = 1 - Math.pow(1 - progress, 3)
    
    animatedStats.papers = Math.floor(targets.papers * ease)
    animatedStats.researchers = Math.floor(targets.researchers * ease)
    animatedStats.hours = Math.floor(targets.hours * ease)
    
    if (progress < 1) requestAnimationFrame(step)
  }
  
  requestAnimationFrame(step)
}

const handleScroll = () => {
  isScrolled.value = window.scrollY > 50
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  initNeuralAnimation()
  setTimeout(animateStats, 300)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  if (animationFrame) cancelAnimationFrame(animationFrame)
})
</script>

<style scoped>
/* ===== Base ===== */
.landing {
  min-height: 100vh;
  background: #030712;
  color: #f1f5f9;
  overflow-x: hidden;
  overflow-y: auto;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ===== Neural Background ===== */
.bg-neural {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.neural-canvas {
  width: 100%;
  height: 100%;
}

.gradient-overlay {
  position: absolute;
  inset: 0;
  background: 
    radial-gradient(ellipse 70% 50% at 50% 0%, rgba(99, 102, 241, 0.12), transparent),
    radial-gradient(ellipse 50% 50% at 80% 50%, rgba(139, 92, 246, 0.08), transparent),
    radial-gradient(ellipse 40% 40% at 20% 80%, rgba(6, 182, 212, 0.06), transparent),
    linear-gradient(to bottom, transparent, #030712);
}

/* ===== Navigation ===== */
.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 20px 48px;
  transition: all 0.3s;
}

.nav-scrolled {
  background: rgba(3, 7, 18, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding: 16px 48px;
}

.nav-container {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-icon {
  flex-shrink: 0;
}

.brand-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #06b6d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.nav-links {
  display: flex;
  gap: 40px;
}

.nav-links a {
  color: #94a3b8;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-links a:hover {
  color: #f1f5f9;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-text {
  padding: 10px 16px;
  color: #94a3b8;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s;
}

.btn-text:hover {
  color: #f1f5f9;
}

.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
}

/* ===== Hero ===== */
.hero {
  position: relative;
  z-index: 1;
  padding: 180px 48px 100px;
  overflow: hidden;
}

/* Floating Orbs */
.hero-orbs {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.4), transparent 70%);
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3), transparent 70%);
  top: 40%;
  right: 15%;
  animation-delay: -7s;
  animation-duration: 25s;
}

.orb-3 {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, rgba(6, 182, 212, 0.3), transparent 70%);
  bottom: 20%;
  left: 30%;
  animation-delay: -14s;
  animation-duration: 22s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -30px) scale(1.05); }
  50% { transform: translate(-20px, 20px) scale(0.95); }
  75% { transform: translate(20px, 10px) scale(1.02); }
}

/* Orbit Decoration */
.hero-orbit {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 800px;
  height: 800px;
  pointer-events: none;
}

.orbit-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  border: 1px dashed rgba(99, 102, 241, 0.15);
  border-radius: 50%;
}

.orbit-1 {
  width: 400px;
  height: 400px;
  margin: -200px 0 0 -200px;
  animation: orbitSpin 30s linear infinite;
}

.orbit-2 {
  width: 550px;
  height: 550px;
  margin: -275px 0 0 -275px;
  animation: orbitSpin 45s linear infinite reverse;
}

.orbit-3 {
  width: 700px;
  height: 700px;
  margin: -350px 0 0 -350px;
  animation: orbitSpin 60s linear infinite;
}

@keyframes orbitSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.orbit-dot {
  position: absolute;
  top: 0;
  left: 50%;
  width: 8px;
  height: 8px;
  margin: -4px 0 0 -4px;
  background: linear-gradient(135deg, #6366f1, #06b6d4);
  border-radius: 50%;
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.6);
}

.orbit-2 .orbit-dot {
  width: 6px;
  height: 6px;
  margin: -3px 0 0 -3px;
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
}

.orbit-3 .orbit-dot {
  width: 4px;
  height: 4px;
  margin: -2px 0 0 -2px;
  background: linear-gradient(135deg, #06b6d4, #22d3ee);
}

.hero-container {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
  position: relative;
  z-index: 2;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 100px;
  font-size: 13px;
  font-weight: 500;
  color: #a5b4fc;
  margin-bottom: 32px;
}

.badge-pulse {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.hero-title {
  font-size: 56px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -1.5px;
  margin-bottom: 24px;
}

.title-highlight {
  background: linear-gradient(90deg, #a5b4fc, #06b6d4, #a5b4fc);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shimmer 4s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { background-position: 0% center; }
  50% { background-position: 100% center; }
}

.hero-desc {
  font-size: 18px;
  line-height: 1.7;
  color: #94a3b8;
  max-width: 560px;
  margin: 0 auto 40px;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 64px;
}

.btn-hero {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 28px;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: white;
  text-decoration: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-hero:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.35);
}

.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 28px;
  background: transparent;
  color: #94a3b8;
  text-decoration: none;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-ghost:hover {
  border-color: rgba(148, 163, 184, 0.4);
  color: #f1f5f9;
}

.hero-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 48px;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #f1f5f9, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(148, 163, 184, 0.15);
}

/* ===== Preview Window ===== */
.hero-preview {
  max-width: 1000px;
  margin: 80px auto 0;
  position: relative;
  z-index: 2;
  animation: previewFloat 6s ease-in-out infinite;
}

@keyframes previewFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.preview-window {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.1);
  transition: all 0.4s ease;
}

.preview-window:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 30px 80px rgba(99, 102, 241, 0.15);
  border-radius: 12px;
  overflow: hidden;
  backdrop-filter: blur(12px);
  box-shadow: 0 40px 80px rgba(0, 0, 0, 0.4);
}

.window-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: rgba(30, 41, 59, 0.5);
  border-bottom: 1px solid rgba(148, 163, 184, 0.08);
}

.window-dots {
  display: flex;
  gap: 8px;
}

.window-dots span {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #334155;
}

.window-dots span:nth-child(1) { background: #f87171; }
.window-dots span:nth-child(2) { background: #fbbf24; }
.window-dots span:nth-child(3) { background: #4ade80; }

.window-title {
  font-size: 13px;
  color: #64748b;
}

.window-content {
  display: grid;
  grid-template-columns: 260px 1fr;
  min-height: 360px;
}

.preview-sidebar {
  padding: 16px;
  border-right: 1px solid rgba(148, 163, 184, 0.08);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.08);
}

.sidebar-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
}

.sidebar-header svg {
  color: #64748b;
}

.paper-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.paper-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.paper-item:hover {
  background: rgba(99, 102, 241, 0.06);
}

.paper-item.active {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.paper-item svg {
  color: #6366f1;
  flex-shrink: 0;
  margin-top: 2px;
}

.paper-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.paper-name {
  font-size: 13px;
  font-weight: 500;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.paper-meta {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.preview-main {
  padding: 20px;
}

.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.main-header h4 {
  font-size: 15px;
  font-weight: 600;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 100px;
  font-size: 12px;
  color: #10b981;
}

.status-dot {
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.insights-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.insight-item {
  display: flex;
  gap: 14px;
  padding: 16px;
  background: rgba(99, 102, 241, 0.04);
  border: 1px solid rgba(99, 102, 241, 0.1);
  border-radius: 10px;
}

.insight-icon {
  width: 36px;
  height: 36px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6366f1;
  flex-shrink: 0;
}

.insight-content {
  flex: 1;
}

.insight-content strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 4px;
}

.insight-content p {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
  margin: 0;
}

.insight-item.loading .insight-content p::after {
  content: '';
  display: inline-block;
  width: 2px;
  height: 14px;
  background: #6366f1;
  margin-left: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ===== Section Common ===== */
.section-container {
  max-width: 1120px;
  margin: 0 auto;
  padding: 0 48px;
}

.section-header {
  text-align: center;
  margin-bottom: 64px;
}

.section-label {
  display: inline-block;
  padding: 6px 14px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 100px;
  font-size: 12px;
  font-weight: 600;
  color: #a5b4fc;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin-bottom: 16px;
}

.section-desc {
  font-size: 17px;
  color: #94a3b8;
  max-width: 560px;
  margin: 0 auto;
}

/* ===== Features ===== */
.features-section {
  position: relative;
  z-index: 1;
  padding: 120px 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.feature-card {
  position: relative;
  padding: 32px;
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(148, 163, 184, 0.08);
  border-radius: 16px;
  transition: all 0.4s ease;
  overflow: hidden;
}

.feature-card:hover {
  background: rgba(15, 23, 42, 0.6);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at var(--x, 50%) var(--y, 50%), rgba(99, 102, 241, 0.15), transparent 50%);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

.feature-card:hover .card-glow {
  opacity: 1;
}

.card-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.05), transparent);
  transition: none;
  pointer-events: none;
}

.feature-card:hover .card-shine {
  animation: cardShine 0.6s ease-out;
}

@keyframes cardShine {
  0% { left: -100%; }
  100% { left: 100%; }
}

.feature-icon {
  position: relative;
  z-index: 1;
  width: 48px;
  height: 48px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6366f1;
  margin-bottom: 20px;
  transition: all 0.3s;
}

.feature-card:hover .feature-icon {
  background: rgba(99, 102, 241, 0.2);
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
}

.feature-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
}

.feature-desc {
  font-size: 14px;
  color: #94a3b8;
  line-height: 1.6;
}

/* ===== Workflow ===== */
.workflow-section {
  position: relative;
  z-index: 1;
  padding: 120px 0;
  background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.02), transparent);
}

.workflow-steps {
  position: relative;
  max-width: 800px;
  margin: 0 auto;
}

.workflow-line {
  position: absolute;
  left: 24px;
  top: 40px;
  bottom: 40px;
  width: 2px;
  background: rgba(99, 102, 241, 0.1);
  overflow: hidden;
}

.workflow-line::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #6366f1, #06b6d4);
  animation: lineFlow 3s ease-in-out infinite;
}

@keyframes lineFlow {
  0% { transform: translateY(-100%); opacity: 0; }
  20% { opacity: 1; }
  80% { opacity: 1; }
  100% { transform: translateY(100%); opacity: 0; }
}

.step {
  display: flex;
  gap: 32px;
  margin-bottom: 48px;
}

.step:last-child {
  margin-bottom: 0;
}

.step-number {
  width: 48px;
  height: 48px;
  background: #030712;
  border: 2px solid rgba(99, 102, 241, 0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: #6366f1;
  flex-shrink: 0;
  position: relative;
  z-index: 2;
  transition: all 0.3s;
}

.step-number::before {
  content: '';
  position: absolute;
  top: -6px;
  left: -6px;
  right: -6px;
  bottom: -6px;
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 50%;
  animation: stepPulse 2s ease-in-out infinite;
}

.step:nth-child(2) .step-number::before { animation-delay: 0.5s; }
.step:nth-child(3) .step-number::before { animation-delay: 1s; }
.step:nth-child(4) .step-number::before { animation-delay: 1.5s; }

@keyframes stepPulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.15); opacity: 0; }
}

.step:hover .step-number {
  border-color: #6366f1;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
}

.step-content {
  flex: 1;
  padding: 24px;
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(148, 163, 184, 0.08);
  border-radius: 12px;
}

.step-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.step-desc {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 16px;
}

.step-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #94a3b8;
}

.step-list li svg {
  color: #10b981;
  flex-shrink: 0;
}

/* ===== Powered By ===== */
.powered-section {
  position: relative;
  z-index: 1;
  padding: 60px 48px 80px;
  border-top: 1px solid rgba(148, 163, 184, 0.08);
}

.powered-label {
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 1px;
  color: #475569;
  margin-bottom: 36px;
}

.powered-row {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 48px;
  max-width: 1000px;
  margin: 0 auto;
}

.powered-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #475569;
  transition: all 0.3s;
  padding: 8px 12px;
  border-radius: 8px;
}

.powered-item:hover {
  color: #e2e8f0;
  background: rgba(99, 102, 241, 0.1);
  transform: translateY(-2px);
}

.powered-item svg {
  width: 24px;
  height: 24px;
  opacity: 0.6;
  transition: all 0.3s;
}

.powered-item:hover svg {
  opacity: 1;
  transform: scale(1.1);
}

.powered-item span {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.3px;
}

/* ===== CTA ===== */
.cta-section {
  position: relative;
  z-index: 1;
  padding: 160px 48px;
  text-align: center;
  overflow: hidden;
}

.cta-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.cta-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
}

.cta-orb-1 {
  width: 400px;
  height: 400px;
  background: rgba(99, 102, 241, 0.25);
  top: 20%;
  left: 15%;
  animation: ctaFloat 8s ease-in-out infinite;
}

.cta-orb-2 {
  width: 350px;
  height: 350px;
  background: rgba(139, 92, 246, 0.2);
  top: 30%;
  right: 15%;
  animation: ctaFloat 10s ease-in-out infinite reverse;
}

.cta-orb-3 {
  width: 300px;
  height: 300px;
  background: rgba(6, 182, 212, 0.15);
  bottom: 15%;
  left: 40%;
  animation: ctaFloat 12s ease-in-out infinite;
}

@keyframes ctaFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, -20px) scale(1.05); }
  66% { transform: translate(-20px, 10px) scale(0.95); }
}

.cta-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse 60% 60% at 50% 50%, black, transparent);
}

.cta-content {
  position: relative;
  z-index: 2;
}

.cta-title {
  font-size: 44px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin-bottom: 16px;
}

.cta-desc {
  font-size: 18px;
  color: #94a3b8;
  margin-bottom: 40px;
}

.btn-cta {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 18px 40px;
  background: #fff;
  color: #030712;
  text-decoration: none;
  border-radius: 12px;
  font-size: 17px;
  font-weight: 700;
  transition: all 0.3s;
  overflow: hidden;
}

.btn-cta:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 48px rgba(255, 255, 255, 0.15);
}

.btn-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.2), transparent);
  animation: btnShine 3s ease-in-out infinite;
}

@keyframes btnShine {
  0%, 100% { left: -100%; }
  50% { left: 100%; }
}

.cta-note {
  display: block;
  margin-top: 16px;
  font-size: 13px;
  color: #64748b;
}

/* ===== Footer ===== */
.footer {
  position: relative;
  z-index: 1;
  padding: 80px 48px 32px;
  border-top: 1px solid rgba(148, 163, 184, 0.08);
}

.footer-container {
  max-width: 1120px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 64px;
  margin-bottom: 48px;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #e2e8f0;
  font-weight: 700;
  margin-bottom: 12px;
}

.footer-logo svg {
  color: #6366f1;
}

.footer-tagline {
  font-size: 14px;
  color: #64748b;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
}

.link-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.col-title {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 4px;
}

.link-col a {
  font-size: 14px;
  color: #64748b;
  text-decoration: none;
  transition: color 0.2s;
}

.link-col a:hover {
  color: #e2e8f0;
}

.footer-bottom {
  max-width: 1120px;
  margin: 0 auto;
  padding-top: 32px;
  border-top: 1px solid rgba(148, 163, 184, 0.08);
  font-size: 13px;
  color: #64748b;
}

/* ===== Responsive ===== */
@media (max-width: 1024px) {
  .nav-links { display: none; }
  
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .window-content {
    grid-template-columns: 1fr;
  }
  
  .preview-sidebar {
    border-right: none;
    border-bottom: 1px solid rgba(148, 163, 184, 0.08);
  }
  
  .paper-list {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 8px;
  }
  
  .paper-item {
    flex-shrink: 0;
    min-width: 200px;
  }
  
  .footer-container {
    grid-template-columns: 1fr;
    gap: 48px;
  }
}

@media (max-width: 768px) {
  .nav { padding: 16px 24px; }
  .nav-scrolled { padding: 12px 24px; }
  
  .hero { padding: 140px 24px 80px; }
  
  .hero-title {
    font-size: 36px;
    letter-spacing: -1px;
  }
  
  .hero-desc { font-size: 16px; }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .hero-stats {
    flex-direction: column;
    gap: 24px;
  }
  
  .stat-divider { display: none; }
  
  .hero-preview { margin-top: 48px; }
  
  .section-container { padding: 0 24px; }
  
  .section-title { font-size: 32px; }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .step {
    flex-direction: column;
    gap: 16px;
  }
  
  .workflow-line { display: none; }
  
  .testimonial-card { padding: 32px; }
  
  .quote-text { font-size: 17px; }
  
  .cta-title { font-size: 32px; }
  
  .footer-links {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .footer { padding: 48px 24px 24px; }
}
</style>
