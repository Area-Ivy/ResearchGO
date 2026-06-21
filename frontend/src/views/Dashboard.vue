<template>
  <div class="dashboard-page">
    <header class="dashboard-header">
      <div>
        <p class="eyebrow">Dashboard</p>
        <h1>Research workspace</h1>
        <p class="subtitle">Track papers, activity, and knowledge shape in one place.</p>
      </div>
      <button class="btn btn-secondary" type="button" :disabled="dashboardLoading" @click="refreshWorkspace">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="1 4 1 10 7 10"></polyline>
          <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
        </svg>
        <span>{{ dashboardLoading ? 'Refreshing' : 'Refresh' }}</span>
      </button>
    </header>

    <section class="knowledge-panel">
      <div class="section-heading">
        <div>
          <h2>Library status</h2>
          <p>Indexing readiness and field coverage for your paper library.</p>
        </div>
        <span class="status-pill" :class="libraryStatusClass">{{ libraryStatusLabel }}</span>
      </div>
      <div class="knowledge-metrics">
        <div class="knowledge-metric">
          <span class="metric-value">{{ knowledge.indexedPaperPercent }}%</span>
          <span class="metric-label">Indexed papers</span>
        </div>
        <div class="knowledge-metric">
          <span class="metric-value metric-text">{{ mainField }}</span>
          <span class="metric-label">Main field</span>
        </div>
        <div class="knowledge-metric">
          <span class="metric-value">{{ activeFieldCount }}</span>
          <span class="metric-label">Active fields</span>
        </div>
      </div>
      <p class="knowledge-copy">{{ libraryStatusDescription }}</p>
    </section>

    <div v-if="dashboardError" class="state state-error">{{ dashboardError }}</div>

    <section class="stat-grid">
      <article class="stat-card">
        <span class="stat-label">Uploaded papers</span>
        <strong class="stat-value">{{ papers.total }}</strong>
        <span class="stat-subtle">All papers in your library</span>
      </article>
      <article class="stat-card">
        <span class="stat-label">Indexed papers</span>
        <strong class="stat-value">{{ papers.indexed }}</strong>
        <span class="stat-subtle">{{ papers.indexed }} ready for retrieval</span>
      </article>
      <article class="stat-card">
        <span class="stat-label">In progress</span>
        <strong class="stat-value">{{ papers.indexing }}</strong>
        <span class="stat-subtle">Uploaded or indexing papers</span>
      </article>
      <article class="stat-card">
        <span class="stat-label">Failed jobs</span>
        <strong class="stat-value">{{ papers.failed }}</strong>
        <span class="stat-subtle">Queue items that need attention</span>
      </article>
      <article class="stat-card">
        <span class="stat-label">Conversations</span>
        <strong class="stat-value">{{ conversations.total }}</strong>
        <span class="stat-subtle">{{ conversations.messagesThisMonth }} messages this month</span>
      </article>
    </section>

    <div v-if="chartError" class="state state-warning">{{ chartError }}</div>

    <section class="chart-grid">
      <article class="chart-panel">
        <div class="section-heading compact">
          <div>
            <h2>Paper status</h2>
            <p>Current upload and indexing distribution.</p>
          </div>
        </div>
        <div class="chart-shell">
          <div ref="paperStatusChartEl" class="echart" aria-label="Paper status chart"></div>
        </div>
      </article>

      <article class="chart-panel">
        <div class="section-heading compact">
          <div>
            <h2>Weekly activity</h2>
            <p>{{ neuralImprint.period }}</p>
          </div>
        </div>
        <div class="chart-shell">
          <div ref="activityChartEl" class="echart" aria-label="Weekly activity chart"></div>
        </div>
      </article>

      <article class="chart-panel chart-panel-wide">
        <div class="section-heading compact">
          <div>
            <h2>Cognitive architecture</h2>
            <p>Field balance inferred from uploaded papers.</p>
          </div>
        </div>
        <div class="chart-shell">
          <div ref="fieldChartEl" class="echart" aria-label="Field distribution chart"></div>
        </div>
      </article>
    </section>

    <section class="detail-grid">
      <article class="detail-panel">
        <div class="section-heading compact">
          <div>
            <h2>Processing queue</h2>
            <p>Recent papers still uploading, indexing, or failed.</p>
          </div>
        </div>
        <div v-if="queue.length" class="stack-list">
          <div v-for="item in queue" :key="item.id" class="stack-item">
            <div>
              <h3>{{ item.operation }}</h3>
              <p>{{ item.statusText }} · {{ item.time }}</p>
            </div>
            <span class="queue-pill" :class="item.status">{{ item.statusText }}</span>
          </div>
        </div>
        <p v-else class="empty-copy">No queued paper jobs right now.</p>
      </article>

      <article class="detail-panel">
        <div class="section-heading compact">
          <div>
            <h2>Recommendations</h2>
            <p>Fresh literature driven by the dominant field in your library.</p>
          </div>
        </div>
        <div v-if="recommendations.length" class="stack-list">
          <a
            v-for="item in recommendations"
            :key="item.id"
            class="stack-item stack-link"
            :href="item.url || '#'"
            :target="item.url ? '_blank' : null"
            rel="noreferrer"
          >
            <div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.category }} · {{ item.authors }}</p>
            </div>
          </a>
        </div>
        <p v-else class="empty-copy">No recommendations available yet.</p>
      </article>
    </section>

  </div>
</template>

<script setup>
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { graphic, init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { getDashboardSummary } from '../api/dashboard'

defineOptions({ name: 'Dashboard' })

use([BarChart, CanvasRenderer, GridComponent, LegendComponent, LineChart, PieChart, TooltipComponent])

const dashboardLoading = ref(false)
const dashboardError = ref('')
const chartError = ref('')

const summary = ref({
  knowledge: {
    entropyValue: 0,
    status: 'LOW_ENTROPY',
    indexedPaperPercent: 0,
    description: 'Your knowledge base is structured.'
  },
  recommendations: [],
  queue: [],
  papers: {
    total: 0,
    indexed: 0,
    indexing: 0,
    failed: 0
  },
  conversations: {
    total: 0,
    messagesThisMonth: 0
  },
  cognitiveArchitecture: {
    labels: [],
    values: []
  },
  neuralImprint: {
    labels: [],
    values: [],
    period: 'Last 30 Weeks'
  }
})

const paperStatusChartEl = ref(null)
const activityChartEl = ref(null)
const fieldChartEl = ref(null)

let paperStatusChart = null
let activityChart = null
let fieldChart = null

const knowledge = computed(() => summary.value.knowledge || {})
const papers = computed(() => summary.value.papers || {})
const conversations = computed(() => summary.value.conversations || {})
const recommendations = computed(() => summary.value.recommendations || [])
const queue = computed(() => summary.value.queue || [])
const cognitiveArchitecture = computed(() => summary.value.cognitiveArchitecture || { labels: [], values: [] })
const neuralImprint = computed(() => summary.value.neuralImprint || { labels: [], values: [], period: 'Last 30 Weeks' })

const fieldRows = computed(() => {
  const labels = cognitiveArchitecture.value.labels || []
  const values = cognitiveArchitecture.value.values || []
  return labels.map((label, index) => ({
    label,
    value: Number(values[index] || 0)
  }))
})

const activeFieldCount = computed(() => fieldRows.value.filter((field) => field.value > 0).length)

const mainField = computed(() => {
  const fields = fieldRows.value.filter((field) => field.value > 0)
  if (!fields.length) return 'Not detected'
  return fields.reduce((best, field) => (field.value > best.value ? field : best), fields[0]).label
})

const libraryStatusLabel = computed(() => {
  if (papers.value.failed > 0) return 'Needs attention'
  if (papers.value.indexing > 0) return 'Indexing'
  if (papers.value.total > 0 && papers.value.indexed === papers.value.total) return 'Ready'
  return 'No papers'
})

const libraryStatusClass = computed(() => ({
  ready: libraryStatusLabel.value === 'Ready',
  indexing: libraryStatusLabel.value === 'Indexing',
  attention: libraryStatusLabel.value === 'Needs attention',
  empty: libraryStatusLabel.value === 'No papers'
}))

const libraryStatusDescription = computed(() => {
  if (papers.value.failed > 0) {
    return `${papers.value.failed} paper job${papers.value.failed === 1 ? '' : 's'} need attention before the library is fully usable.`
  }
  if (papers.value.indexing > 0) {
    return `${papers.value.indexing} paper${papers.value.indexing === 1 ? ' is' : 's are'} still being uploaded or indexed.`
  }
  if (papers.value.total > 0) {
    return `All ${papers.value.total} uploaded paper${papers.value.total === 1 ? ' is' : 's are'} indexed and ready for retrieval.`
  }
  return 'Upload papers to start building an indexed research library.'
})

const destroyCharts = () => {
  for (const chart of [paperStatusChart, activityChart, fieldChart]) {
    if (chart) chart.dispose()
  }
  paperStatusChart = null
  activityChart = null
  fieldChart = null
}

const resizeCharts = () => {
  for (const chart of [paperStatusChart, activityChart, fieldChart]) {
    if (chart) chart.resize()
  }
}

const chartTextStyle = {
  color: '#cbd5e1',
  fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'
}

const renderCharts = async () => {
  await nextTick()
  destroyCharts()

  if (paperStatusChartEl.value) {
    const statusRows = [
      { name: 'Indexed', value: Number(papers.value.indexed || 0) },
      { name: 'In progress', value: Number(papers.value.indexing || 0) },
      { name: 'Failed', value: Number(papers.value.failed || 0) }
    ]
    const hasStatusData = statusRows.some((item) => item.value > 0)
    paperStatusChart = init(paperStatusChartEl.value, null, { renderer: 'canvas' })
    paperStatusChart.setOption({
      color: ['#38bdf8', '#34d399', '#f87171'],
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(8, 13, 28, 0.94)',
        borderColor: 'rgba(148, 163, 184, 0.22)',
        textStyle: chartTextStyle
      },
      legend: {
        bottom: 0,
        icon: 'circle',
        textStyle: chartTextStyle
      },
      series: [
        {
          name: 'Papers',
          type: 'pie',
          radius: ['54%', '74%'],
          center: ['50%', '43%'],
          avoidLabelOverlap: true,
          minAngle: 8,
          label: {
            color: '#e2e8f0',
            formatter: '{b}\n{c}'
          },
          labelLine: {
            lineStyle: { color: 'rgba(148, 163, 184, 0.45)' }
          },
          itemStyle: {
            borderColor: '#0b1120',
            borderWidth: 3
          },
          emphasis: {
            scaleSize: 6
          },
          data: hasStatusData ? statusRows : [{ name: 'No papers', value: 1, itemStyle: { color: 'rgba(148, 163, 184, 0.28)' } }]
        }
      ]
    })
  }

  if (activityChartEl.value) {
    activityChart = init(activityChartEl.value, null, { renderer: 'canvas' })
    activityChart.setOption({
      color: ['#38bdf8'],
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(8, 13, 28, 0.94)',
        borderColor: 'rgba(148, 163, 184, 0.22)',
        textStyle: chartTextStyle
      },
      grid: {
        left: 42,
        right: 18,
        top: 22,
        bottom: 34
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: neuralImprint.value.labels || [],
        axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.24)' } },
        axisTick: { show: false },
        axisLabel: {
          color: '#94a3b8',
          interval: 4
        },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: { color: '#94a3b8' },
        splitLine: { lineStyle: { color: 'rgba(71, 85, 105, 0.22)' } }
      },
      series: [
        {
          name: 'Activity',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 3 },
          areaStyle: {
            opacity: 0.22,
            color: new graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(56, 189, 248, 0.44)' },
              { offset: 1, color: 'rgba(56, 189, 248, 0.02)' }
            ])
          },
          data: neuralImprint.value.values || []
        }
      ]
    })
  }

  if (fieldChartEl.value) {
    fieldChart = init(fieldChartEl.value, null, { renderer: 'canvas' })
    fieldChart.setOption({
      color: ['#8b5cf6'],
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(8, 13, 28, 0.94)',
        borderColor: 'rgba(148, 163, 184, 0.22)',
        textStyle: chartTextStyle
      },
      grid: {
        left: 42,
        right: 18,
        top: 20,
        bottom: 38
      },
      xAxis: {
        type: 'category',
        data: cognitiveArchitecture.value.labels || [],
        axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.24)' } },
        axisTick: { show: false },
        axisLabel: {
          color: '#94a3b8'
        },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        max: 100,
        axisLabel: { color: '#94a3b8', formatter: '{value}%' },
        splitLine: { lineStyle: { color: 'rgba(71, 85, 105, 0.22)' } }
      },
      series: [
        {
          name: 'Field weight',
          type: 'bar',
          barMaxWidth: 44,
          itemStyle: {
            borderRadius: [8, 8, 0, 0],
            color: new graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#38bdf8' },
              { offset: 0.58, color: '#8b5cf6' },
              { offset: 1, color: '#312e81' }
            ])
          }
        },
        {
          type: 'bar',
          barGap: '-100%',
          barMaxWidth: 44,
          data: new Array((cognitiveArchitecture.value.values || []).length).fill(100),
          itemStyle: {
            color: 'rgba(148, 163, 184, 0.08)',
            borderRadius: [8, 8, 0, 0]
          },
          silent: true,
          z: -1
        }
      ].map((series) => ({
        ...series,
        data: series.data || cognitiveArchitecture.value.values || []
      }))
    })
  }
}

const loadDashboard = async () => {
  dashboardLoading.value = true
  dashboardError.value = ''
  chartError.value = ''

  try {
    summary.value = await getDashboardSummary()
  } catch (err) {
    dashboardError.value = err.response?.data?.detail || 'Failed to load dashboard summary.'
    destroyCharts()
    dashboardLoading.value = false
    return
  }

  try {
    await renderCharts()
  } catch (err) {
    console.error('Dashboard chart render failed:', err)
    chartError.value = 'Dashboard data loaded, but charts failed to render.'
    destroyCharts()
  } finally {
    dashboardLoading.value = false
  }
}

const refreshWorkspace = async () => {
  await loadDashboard()
}

onMounted(() => {
  loadDashboard()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  destroyCharts()
})
</script>

<style scoped>
.dashboard-page {
  min-height: calc(100vh - 68px);
  display: flex;
  flex-direction: column;
  gap: 18px;
  color: var(--text-primary);
}

.dashboard-header,
.memory-header,
.memory-footer,
.actions,
.doc-stats,
.knowledge-metrics,
.detail-grid {
  display: flex;
  align-items: stretch;
  gap: 18px;
}

.dashboard-header {
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

.dashboard-header h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 34px;
  font-weight: 850;
  line-height: 1.1;
}

.subtitle {
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 15px;
}

.knowledge-panel,
.settings-panel,
.memory-panel,
.stat-card,
.chart-panel,
.detail-panel {
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  background: var(--gradient-surface);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(18px);
}

.knowledge-panel {
  padding: 22px;
}

.settings-panel {
  padding: 20px;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-top: 16px;
  padding: 16px;
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  background: rgba(8, 13, 28, 0.44);
}

.setting-row h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
}

.setting-row p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.switch {
  position: relative;
  flex: 0 0 auto;
  width: 58px;
  height: 32px;
  cursor: pointer;
}

.switch input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.switch-track {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: rgba(71, 85, 105, 0.62);
  border: 1px solid rgba(148, 163, 184, 0.24);
  transition: background 0.2s ease, border-color 0.2s ease;
}

.switch-thumb {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: #f8fafc;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s ease;
}

.switch input:checked + .switch-track {
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.95), rgba(139, 92, 246, 0.95));
  border-color: rgba(56, 189, 248, 0.4);
}

.switch input:checked + .switch-track .switch-thumb {
  transform: translateX(26px);
}

.switch input:disabled + .switch-track {
  opacity: 0.58;
  cursor: not-allowed;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.section-heading.compact h2 {
  font-size: 20px;
}

.section-heading h2 {
  margin: 0;
  font-size: 24px;
  line-height: 1.1;
}

.section-heading p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.status-pill,
.queue-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.status-pill {
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.28);
  color: #7dd3fc;
}

.status-pill.ready {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.3);
  color: #86efac;
}

.status-pill.indexing {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.28);
  color: #7dd3fc;
}

.status-pill.attention {
  background: rgba(248, 113, 113, 0.12);
  border-color: rgba(248, 113, 113, 0.32);
  color: #fca5a5;
}

.status-pill.empty {
  background: rgba(148, 163, 184, 0.12);
  border-color: rgba(148, 163, 184, 0.28);
  color: #cbd5e1;
}

.knowledge-metrics {
  margin-top: 24px;
}

.knowledge-metric {
  flex: 1;
  padding: 16px;
  border-radius: 8px;
  background: rgba(8, 13, 28, 0.52);
  border: 1px solid var(--border-primary);
}

.metric-value {
  display: block;
  font-size: 30px;
  font-weight: 850;
  line-height: 1;
}

.metric-text {
  min-height: 30px;
  overflow-wrap: anywhere;
  font-size: clamp(18px, 2vw, 28px);
  line-height: 1.12;
}

.metric-label {
  display: block;
  margin-top: 8px;
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 750;
  text-transform: uppercase;
}

.knowledge-copy {
  margin: 18px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.stat-grid,
.chart-grid {
  display: grid;
  gap: 18px;
}

.stat-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.stat-card {
  padding: 18px;
}

.stat-label {
  display: block;
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.stat-value {
  display: block;
  margin-top: 12px;
  color: var(--text-primary);
  font-size: 36px;
  line-height: 1;
}

.stat-subtle {
  display: block;
  margin-top: 10px;
  color: var(--text-secondary);
  font-size: 13px;
}

.chart-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.chart-panel {
  padding: 20px;
}

.chart-panel-wide {
  grid-column: 1 / -1;
}

.chart-shell {
  position: relative;
  min-height: 280px;
  margin-top: 18px;
}

.echart {
  width: 100%;
  height: 280px;
}

.detail-grid {
  align-items: stretch;
}

.detail-panel {
  flex: 1;
  padding: 20px;
}

.stack-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 18px;
}

.stack-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  background: rgba(8, 13, 28, 0.44);
}

.stack-link {
  color: inherit;
  text-decoration: none;
}

.stack-item h3 {
  margin: 0;
  font-size: 15px;
  line-height: 1.45;
}

.stack-item p {
  margin: 6px 0 0;
  color: var(--text-tertiary);
  font-size: 13px;
}

.queue-pill {
  flex: 0 0 auto;
}

.queue-pill.processing {
  background: rgba(139, 92, 246, 0.12);
  border: 1px solid rgba(139, 92, 246, 0.32);
  color: #c4b5fd;
}

.queue-pill.failed {
  background: rgba(248, 113, 113, 0.12);
  border: 1px solid rgba(248, 113, 113, 0.32);
  color: #fca5a5;
}

.empty-copy {
  margin: 18px 0 0;
  color: var(--text-tertiary);
  font-size: 14px;
}

.memory-panel {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
}

.memory-header {
  justify-content: space-between;
  align-items: flex-start;
}

.title-block h2 {
  margin: 0 0 8px;
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 800;
  line-height: 1.1;
}

.file-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--text-tertiary);
  font-size: 13px;
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

.state-warning {
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.32);
  color: #fde68a;
}

.editor-panel {
  position: relative;
  flex: 1;
  min-height: 460px;
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  background: rgba(8, 13, 28, 0.78);
  overflow: hidden;
}

.memory-editor {
  width: 100%;
  height: 100%;
  min-height: 460px;
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

.memory-footer.collapsed {
  padding-top: 4px;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
}

.toggle-icon {
  transition: transform 0.2s ease;
}

.toggle-icon.expanded {
  transform: rotate(180deg);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1100px) {
  .chart-grid,
  .detail-grid,
  .stat-grid {
    grid-template-columns: 1fr;
    display: grid;
  }

}

@media (max-width: 768px) {
  .dashboard-page {
    min-height: calc(100vh - 64px);
  }

  .dashboard-header,
  .memory-header,
  .memory-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .dashboard-header h1 {
    font-size: 28px;
  }

  .knowledge-metrics {
    flex-direction: column;
  }

  .actions {
    width: 100%;
  }

  .btn {
    flex: 1;
  }

  .stack-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .editor-panel,
  .memory-editor {
    min-height: 420px;
  }
}
</style>
