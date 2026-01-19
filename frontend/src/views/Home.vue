<template>
  <div class="dashboard">
    <!-- Header Section -->
    <div class="dashboard-header">
      <div class="welcome-section">
        <h1 class="page-title">Welcome back, Architect of the Future.</h1>
        <p class="page-subtitle">Compiling today's insights for your neural networks.</p>
    </div>
      <div class="header-actions">
        <button class="btn btn-secondary">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"></path>
          </svg>
          <span>Computer Science</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
        <button class="notification-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
          </button>
        </div>
      </div>

    <!-- Top Stats Grid -->
    <div class="stats-grid">
      <!-- Photon Usage Card -->
      <div class="card stats-card">
        <div class="stats-header">
          <div class="stats-label">
            <span class="indicator"></span>
            <span>Photon Usage</span>
          </div>
          <span class="badge badge-success">Pro Plan</span>
        </div>
        <div class="stats-value">
          <h2>{{ photonUsage }}</h2>
          <span class="stats-unit">/ {{ totalPhotons }} Monthly Credits</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: photonPercentage + '%' }"></div>
        </div>
        <p class="stats-info">
          Your research activity is high. You have enough Photons for approximately 
          <strong>{{ remainingDeepPapers }} more deep paper analyses</strong>.
        </p>
        <p class="stats-hint">Reach 2000 to unlock Grand Prize</p>
      </div>

      <!-- Knowledge Entropy Card -->
      <div class="card stats-card">
        <div class="stats-header">
          <div class="stats-label">
            <span class="indicator indicator-success"></span>
            <span>Knowledge Entropy</span>
          </div>
        </div>
        <div class="entropy-display">
          <div class="entropy-circle">
            <svg width="160" height="160" viewBox="0 0 160 160">
              <circle cx="80" cy="80" r="70" fill="none" stroke="rgba(99, 102, 241, 0.1)" stroke-width="8"/>
              <circle cx="80" cy="80" r="70" fill="none" stroke="url(#entropyGradient)" stroke-width="8" 
                      stroke-dasharray="440" stroke-dashoffset="330" stroke-linecap="round"
                      transform="rotate(-90 80 80)"/>
              <defs>
                <linearGradient id="entropyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#6366F1;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#00ff88;stop-opacity:1" />
                </linearGradient>
              </defs>
            </svg>
            <div class="entropy-value">
              <div class="entropy-number">{{ entropyValue }}</div>
              <div class="entropy-label">ENTROPY</div>
            </div>
          </div>
        </div>
        <div class="entropy-status">
          <div class="status-item">
            <span class="status-label">System Status</span>
            <span class="status-badge badge-success">LOW ENTROPY</span>
          </div>
          <p class="status-description">
            Your knowledge base is structured. 0% of concepts are interconnected.
          </p>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="content-grid">
      <!-- Daily Recommendations -->
      <div class="card recommendations-card">
        <div class="card-header">
          <h3>Daily Recommendations</h3>
          <a href="#" class="view-all-link">View All</a>
        </div>
        <div class="recommendations-list">
          <div v-for="paper in dailyRecommendations" :key="paper.id" class="recommendation-item">
            <div class="recommendation-tag">{{ paper.category }}</div>
            <h4 class="recommendation-title">{{ paper.title }}</h4>
            <p class="recommendation-authors">{{ paper.authors }}</p>
            <button class="btn-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
            </svg>
          </button>
          </div>
        </div>
      </div>

      <!-- Field Progress -->
      <div class="card field-progress-card">
        <div class="card-header">
          <h3>Field Progress</h3>
          <a href="#" class="view-all-link">More News</a>
        </div>
        <div class="field-progress-list">
          <div v-for="news in fieldProgress" :key="news.id" class="progress-item">
            <div class="progress-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
          </svg>
            </div>
            <div class="progress-content">
              <h4 class="progress-title">{{ news.title }}</h4>
              <p class="progress-source">{{ news.source }} • {{ news.time }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Grid -->
    <div class="analysis-grid">
      <!-- Cognitive Architecture -->
      <div class="card chart-card">
        <div class="card-header">
          <div class="chart-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 3v18h18"></path>
              <path d="m19 9-5 5-4-4-3 3"></path>
            </svg>
            <h3>Cognitive Architecture</h3>
          </div>
        </div>
        <div class="chart-container">
          <canvas ref="radarChart"></canvas>
        </div>
        <div class="chart-legend">
          <span class="legend-item">Updated: Today</span>
        </div>
      </div>

      <!-- Neural Imprint -->
      <div class="card chart-card">
        <div class="card-header">
          <div class="chart-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
          </svg>
            <h3>Neural Imprint</h3>
          </div>
          <span class="chart-period">Last 30 Weeks</span>
        </div>
        <div class="chart-container">
          <canvas ref="lineChart"></canvas>
        </div>
      </div>

      <!-- Background Synthesis Queue -->
      <div class="card queue-card">
        <div class="card-header">
          <div class="chart-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="9" y1="9" x2="15" y2="9"></line>
            </svg>
            <h3>Background Synthesis Queue</h3>
          </div>
          <span class="agent-status">
            <span class="status-dot"></span>
            AGENT ONLINE
          </span>
        </div>
        <div class="queue-content">
          <table class="queue-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>OPERATION</th>
                <th>STATUS</th>
                <th>TIME</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="task in queueTasks" :key="task.id">
                <td class="task-id">{{ task.id }}</td>
                <td class="task-operation">{{ task.operation }}</td>
                <td>
                  <span class="badge" :class="'badge-' + task.status">
                    <span v-if="task.status === 'processing'" class="spinner"></span>
                    {{ task.statusText }}
                  </span>
                </td>
                <td class="task-time">{{ task.time }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Dashboard'
}
</script>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

// Stats Data
const photonUsage = ref(389)
const totalPhotons = ref(2000)
const entropyValue = ref(2)

const photonPercentage = computed(() => (photonUsage.value / totalPhotons.value) * 100)
const remainingDeepPapers = computed(() => Math.floor((totalPhotons.value - photonUsage.value) / 10))

// Daily Recommendations Mock Data
const dailyRecommendations = ref([
  {
    id: 1,
    category: 'Computer Science',
    title: 'Physics-informed machine learning',
    authors: 'G. Karniadakis, I. Kevrekidis, Lu Lu et al. • 2021'
  },
  {
    id: 2,
    category: 'Computer Science',
    title: 'Fashion-MNIST: a Novel Image Dataset for Benchmarking Machine Learning Algorithms',
    authors: 'Han Xiao, Kashif Rasul, Roland Vollgraf • 2017'
  },
  {
    id: 3,
    category: 'Computer Science',
    title: 'A Survey on Bias and Fairness in Machine Learning',
    authors: 'Ninareh Mehrabi, Fred Morstatter, N. Saxena et al. • 2019'
  }
])

// Field Progress Mock Data
const fieldProgress = ref([
  {
    id: 1,
    title: 'OpenAI announces Sora: video generation from text',
    source: 'OpenAI',
    time: '1d ago'
  },
  {
    id: 2,
    title: 'New sorting algorithm discovered by AI',
    source: 'Nature',
    time: '5h ago'
  },
  {
    id: 3,
    title: 'Google releases Gemini 1.5 with 1M context window',
    source: 'AI Blog',
    time: '2h ago'
  }
])

// Queue Tasks Mock Data
const queueTasks = ref([
  {
    id: 'TX-9999',
    operation: 'Processing PDF: NIPS-2017-attention-is-all-you-need-Paper.pdf',
    status: 'processing',
    statusText: 'Processing',
    time: '3123s'
  }
])

// Chart refs
const radarChart = ref(null)
const lineChart = ref(null)

// Initialize Charts
onMounted(() => {
  // Radar Chart - Cognitive Architecture
  if (radarChart.value) {
    new Chart(radarChart.value, {
      type: 'radar',
      data: {
        labels: ['Algorithms', 'Data', 'Systems', 'AI/ML', 'Theory', 'Security'],
        datasets: [{
          label: 'Knowledge Level',
          data: [75, 60, 85, 90, 55, 70],
          backgroundColor: 'rgba(102, 126, 234, 0.2)',
          borderColor: 'rgba(102, 126, 234, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(102, 126, 234, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            beginAtZero: true,
            max: 100,
            ticks: {
              color: '#6b7280',
              backdropColor: 'transparent'
            },
            grid: {
              color: 'rgba(102, 126, 234, 0.1)'
            },
            pointLabels: {
              color: '#a5adc8',
              font: {
                size: 12
              }
            }
          }
        },
        plugins: {
          legend: {
            display: false
          }
        }
      }
    })
  }

  // Line Chart - Neural Imprint
  if (lineChart.value) {
    new Chart(lineChart.value, {
      type: 'line',
      data: {
        labels: Array.from({ length: 30 }, (_, i) => `W${i + 1}`),
        datasets: [{
          label: 'Activity',
          data: Array.from({ length: 30 }, () => Math.floor(Math.random() * 100)),
          borderColor: 'rgba(102, 126, 234, 1)',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointBackgroundColor: 'rgba(102, 126, 234, 1)',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            display: false
          },
          y: {
            display: false,
            beginAtZero: true
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            enabled: true,
            mode: 'index',
            intersect: false
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        }
      }
    })
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1600px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  gap: 24px;
}

.welcome-section {
  flex: 1;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.notification-btn {
  width: 44px;
  height: 44px;
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

.notification-btn:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.stats-card {
  padding: 24px;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-primary);
  box-shadow: 0 0 10px var(--accent-primary);
  animation: pulse 2s ease-in-out infinite;
}

.indicator-success {
  background: var(--accent-success);
  box-shadow: 0 0 10px var(--accent-success);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.stats-value {
  margin-bottom: 16px;
}

.stats-value h2 {
  font-size: 48px;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  line-height: 1;
}

.stats-unit {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-left: 8px;
}

.progress-bar {
  height: 8px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 16px;
}

.progress-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: 4px;
  transition: width 0.6s ease;
  box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
}

.stats-info {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.6;
}

.stats-hint {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* Knowledge Entropy */
.entropy-display {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 24px 0;
}

.entropy-circle {
  position: relative;
  width: 160px;
  height: 160px;
}

.entropy-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.entropy-number {
  font-size: 42px;
  font-weight: 700;
  background: var(--gradient-success);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.entropy-label {
  font-size: 11px;
  color: var(--text-tertiary);
  letter-spacing: 1px;
  margin-top: 4px;
}

.entropy-status {
  padding-top: 16px;
  border-top: 1px solid var(--border-primary);
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.status-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.status-badge {
  font-size: 11px;
}

.status-description {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-primary);
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.view-all-link {
  font-size: 13px;
  color: var(--accent-primary);
  text-decoration: none;
  transition: color 0.3s ease;
}

.view-all-link:hover {
  color: var(--accent-secondary);
}

/* Recommendations */
.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-item {
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 10px;
  transition: all 0.3s ease;
  position: relative;
}

.recommendation-item:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
}

.recommendation-tag {
  display: inline-block;
  font-size: 11px;
  color: var(--accent-primary);
  background: rgba(102, 126, 234, 0.1);
  padding: 4px 10px;
  border-radius: 12px;
  margin-bottom: 8px;
  font-weight: 500;
}

.recommendation-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.recommendation-authors {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
}

.btn-icon {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-primary);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-icon:hover {
  color: var(--accent-primary);
  border-color: var(--border-glow);
}

/* Field Progress */
.field-progress-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 10px;
  transition: all 0.3s ease;
}

.progress-item:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
}

.progress-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.progress-content {
  flex: 1;
  min-width: 0;
}

.progress-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px 0;
  line-height: 1.3;
}

.progress-source {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
}

/* Analysis Grid */
.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.chart-card {
  padding: 24px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-title svg {
  color: var(--accent-primary);
}

.chart-period {
  font-size: 12px;
  color: var(--text-tertiary);
}

.chart-container {
  height: 240px;
  margin: 20px 0;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-primary);
}

.legend-item {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* Queue Card */
.queue-card {
  grid-column: 1 / -1;
}

.agent-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--accent-success);
  letter-spacing: 0.5px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-success);
  box-shadow: 0 0 10px var(--accent-success);
  animation: pulse 2s ease-in-out infinite;
}

.queue-content {
  overflow-x: auto;
}

.queue-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.queue-table thead th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 11px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
}

.queue-table tbody td {
  padding: 16px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-primary);
  font-size: 13px;
  }
  
.queue-table tbody tr:last-child td {
  border-bottom: none;
}

.queue-table tbody tr:hover {
  background: rgba(102, 126, 234, 0.05);
}

.task-id {
  font-family: 'Courier New', monospace;
  color: var(--text-tertiary);
}

.task-operation {
  font-weight: 500;
}

.task-time {
  color: var(--text-tertiary);
  font-family: 'Courier New', monospace;
}

.badge-processing {
  background: rgba(102, 126, 234, 0.15);
  color: var(--accent-primary);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  }
  
/* Responsive */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
  }

  .stats-grid,
  .content-grid,
  .analysis-grid {
    grid-template-columns: 1fr;
  }

  .stats-value h2 {
    font-size: 36px;
  }
  
  .queue-content {
    overflow-x: scroll;
  }
}
</style>
