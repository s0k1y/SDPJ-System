<template>
  <div class="dashboard">
    <div class="dashboard-inner">
      <h1 class="page-title">仪表盘</h1>

      <p class="info-hint">数据实时更新，可能有短暂延迟</p>

      <div class="stats-section">
        <div class="stats-grid">
          <div class="stat-item" v-for="stat in statsCards" :key="stat.key">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value-row">
              <span class="stat-number">{{ stat.value }}</span>
              <span v-if="stat.suffix" class="stat-unit">{{ stat.suffix }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-header">
          <h2 class="section-title">系统状态</h2>
        </div>

        <div class="status-list">
          <div class="status-row">
            <span class="status-label">运行状态</span>
            <template v-if="!statusLoading">
              <span class="status-dot" :class="getStatusClass(systemStatus)"></span>
              <span class="status-text">{{ getSystemStatusText(systemStatus) }}</span>
            </template>
          </div>
          <div class="status-row">
            <span class="status-label">运行任务</span>
            <span v-if="!statusLoading" class="status-value">{{ runningCount }} 个</span>
          </div>
          <div class="status-row">
            <span class="status-label">等待任务</span>
            <span v-if="!statusLoading" class="status-value">{{ pendingCount }} 个</span>
          </div>
          <div class="status-row">
            <span class="status-label">任务完成</span>
            <span v-if="!statusLoading" class="status-value">{{ completedCount }} 个</span>
          </div>
          <div class="status-row">
            <span class="status-label">任务失败</span>
            <span v-if="!statusLoading" class="status-value">{{ failedCount }} 个</span>
          </div>
        </div>
      </div>

      <TaskList :groups="taskGroups" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../api'
import { getProgress } from '../api/detection'
import { getComplianceStatistics } from '../api/report'
import TaskList from '../components/detection/TaskList.vue'

const systemStatus = ref('idle')
const runningCount = ref(0)
const pendingCount = ref(0)
const completedCount = ref(0)
const failedCount = ref(0)
const statusLoading = ref(true)
const taskGroups = ref([])
let pollTimer = null

const stats = ref({
  totalSamples: 0,
  compliantSamples: 0,
  nonCompliantSamples: 0,
  complianceRate: 0,
  avgIterationCount: null
})

const recentTasks = ref([])

const statsCards = computed(() => [
  { key: 'total', label: '检测样本总数', value: stats.value.totalSamples },
  { key: 'compliant', label: '合规样本', value: stats.value.compliantSamples },
  { key: 'non-compliant', label: '违规样本', value: stats.value.nonCompliantSamples },
  { key: 'rate', label: '合规率', value: stats.value.complianceRate.toFixed(1), suffix: '%' }
])

const getSystemStatusText = (status) => {
  const map = {
    idle: '空闲', detecting: '检测中', generating_report: '生成报告中',
    configuring: '配置管理中', error: '异常'
  }
  return map[status] || status
}

const getStatusClass = (status) => {
  return status !== 'error' ? 'dot-online' : ''
}

async function fetchStatus() {
  try {
    const [statusRes, progressRes] = await Promise.allSettled([
      api.get('/status'),
      getProgress()
    ])

    if (statusRes.status === 'fulfilled' && statusRes.value?.data?.status) {
      systemStatus.value = statusRes.value.data.status
    }

    if (progressRes.status === 'fulfilled' && progressRes.value?.success && progressRes.value?.data?.groups) {
      const groups = progressRes.value.data.groups
      taskGroups.value = groups
      recentTasks.value = groups.slice(0, 5).map(g => ({
        task_id: g.task_group_id,
        model_name: g.model_name,
        dataset_count: g.children?.length || 0,
        status: g.status
      }))
      let running = 0, pending = 0, completed = 0, failed = 0
      for (const g of groups) {
        if (g.progress) {
          running += g.progress.running || 0
          pending += g.progress.pending || 0
          completed += g.progress.completed || 0
          failed += g.progress.failed || 0
        }
      }
      runningCount.value = running
      pendingCount.value = pending
      completedCount.value = completed
      failedCount.value = failed
    }
  } catch (e) {
    console.error('fetchStatus error:', e)
  } finally {
    statusLoading.value = false
  }
}

async function loadStats() {
  const statsRes = await getComplianceStatistics().catch(() => null)
  if (statsRes?.success) {
    const d = statsRes.data
    stats.value = {
      totalSamples: d.total,
      compliantSamples: d.compliant,
      nonCompliantSamples: d.non_compliant,
      complianceRate: d.compliance_rate,
      avgIterationCount: d.avg_iteration_count ?? null
    }
  }
}

onMounted(() => {
  loadStats()
  fetchStatus()
  pollTimer = setInterval(fetchStatus, 5000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

.dashboard-inner {
  max-width: 936px;
  margin: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #404040;
  line-height: 32px;
  margin: 0 0 32px;
}

.info-hint {
  font-size: 14px;
  color: #404040;
  line-height: 25px;
  margin: 0 0 22px;
}

.stats-section {
  margin-bottom: 42px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 304px 304px 304px 304px;
  gap: 12px 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 13px;
  color: #8b8b8b;
  line-height: 25px;
}

.stat-value-row {
  display: flex;
  align-items: baseline;
}

.stat-number {
  font-size: 28px;
  color: #404040;
  line-height: 36px;
}

.stat-unit {
  font-size: 18px;
  color: #8b8b8b;
  margin-left: 4px;
}

.section {
  margin-bottom: 42px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 21px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #404040;
  margin: 0;
}

.section-action {
  font-size: 14px;
  color: #404040;
  text-decoration: none;
  line-height: 22px;
}

.section-action:hover {
  opacity: 0.7;
}

.empty-hint {
  font-size: 14px;
  color: #8b8b8b;
  line-height: 25px;
}

.task-list {
  display: flex;
  flex-direction: column;
}

.task-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.task-row:last-child {
  border-bottom: none;
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.task-id {
  font-size: 14px;
  color: #404040;
  font-family: var(--font-family-mono);
}

.task-meta {
  font-size: 13px;
  color: #8b8b8b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-sep {
  color: #d0d0d0;
}

.task-status-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  flex-shrink: 0;
}

.tag-completed {
  background: transparent;
  color: #16a34a;
}

.tag-running {
  background: transparent;
  color: #2563eb;
}

.tag-pending {
  background: #f5f5f5;
  color: #8b8b8b;
}

.tag-failed {
  background: transparent;
  color: #dc2626;
}

.status-list {
  display: flex;
  flex-direction: column;
  width: fit-content;
}

.status-row {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.status-row:last-child {
  border-bottom: none;
}

.status-label {
  font-size: 14px;
  color: #8b8b8b;
  flex-shrink: 0;
  margin-right: 16px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d0d0d0;
  margin-right: 8px;
  flex-shrink: 0;
}

.status-dot.dot-online {
  background: #22c55e;
}

.status-text {
  font-size: 14px;
  color: #404040;
  margin-right: 16px;
}

.status-value {
  font-size: 14px;
  color: #404040;
  font-weight: 500;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
