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
          <h2 class="section-title">最近任务</h2>
          <router-link to="/detection" class="section-action">查看全部</router-link>
        </div>

        <template v-if="loading">
          <el-skeleton :rows="5" animated />
        </template>
        <template v-else>
          <div v-if="recentTasks.length === 0" class="empty-hint">暂无任务</div>
          <div v-else class="task-list">
            <div v-for="task in recentTasks.slice(0, 5)" :key="task.task_id" class="task-row">
              <div class="task-info">
                <span class="task-id">{{ task.task_id }}</span>
                <span class="task-meta">
                  <span>{{ task.model_id }}</span>
                  <span class="meta-sep">·</span>
                  <span>{{ task.dataset_id }}</span>
                </span>
              </div>
              <span class="task-status-tag" :class="`tag-${task.status}`">
                {{ getTaskStatusText(task.status) }}
              </span>
            </div>
          </div>
        </template>
      </div>

      <div class="section">
        <div class="section-header">
          <h2 class="section-title">系统状态</h2>
        </div>

        <template v-if="loading">
          <el-skeleton :rows="4" animated />
        </template>
        <template v-else>
          <div class="status-list">
            <div class="status-row">
              <span class="status-label">运行状态</span>
              <span class="status-dot" :class="getStatusClass(systemStatus)"></span>
              <span class="status-text">{{ getSystemStatusText(systemStatus) }}</span>
            </div>
            <div class="status-row">
              <span class="status-label">运行任务</span>
              <span class="status-value">{{ runningCount }} 个</span>
            </div>
            <div class="status-row">
              <span class="status-label">等待任务</span>
              <span class="status-value">{{ pendingCount }} 个</span>
            </div>
            <div class="status-row">
              <span class="status-label">今日完成</span>
              <span class="status-value">{{ completedToday }} 个</span>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import { getProgress } from '../api/detection'
import { getComplianceStatistics } from '../api/report'

const loading = ref(false)
const systemStatus = ref('unknown')
const runningCount = ref(0)
const pendingCount = ref(0)
const completedToday = ref(0)

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
    configuring: '配置管理中', error: '异常', unknown: '未知'
  }
  return map[status] || status
}

const getStatusClass = (status) => {
  return (status !== 'error' && status !== 'unknown') ? 'dot-online' : ''
}

const getTaskStatusText = (status) => {
  const map = { completed: '已完成', running: '运行中', pending: '等待中', failed: '失败' }
  return map[status] || status
}

onMounted(async () => {
  loading.value = true
  try {
    const statusRes = await api.get('/status')
    systemStatus.value = statusRes?.status || 'unknown'
  } catch { systemStatus.value = 'unknown' }

  try {
    const progressRes = await getProgress()
    if (progressRes.success && progressRes.queue) {
      const queue = progressRes.queue
      recentTasks.value = queue.slice(0, 10)
      runningCount.value = queue.filter(t => t.status === 'running').length
      pendingCount.value = queue.filter(t => t.status === 'pending').length
      completedToday.value = queue.filter(t => t.status === 'completed').length
    }
  } catch { /* default */ }

  try {
    const statsRes = await getComplianceStatistics()
    if (statsRes.success) {
      stats.value = {
        totalSamples: statsRes.total,
        compliantSamples: statsRes.compliant,
        nonCompliantSamples: statsRes.non_compliant,
        complianceRate: statsRes.compliance_rate,
        avgIterationCount: statsRes.avg_iteration_count ?? null
      }
    }
  } catch { /* default */ }
  finally { loading.value = false }
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
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
}

.tag-running {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
}

.tag-pending {
  background: #f5f5f5;
  color: #8b8b8b;
}

.tag-failed {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.status-list {
  display: flex;
  flex-direction: column;
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
  width: 100px;
  flex-shrink: 0;
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

  .status-label {
    width: 80px;
  }
}
</style>
