<template>
  <PageLayout title="仪表盘" max-width="1400px">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <template v-if="loading">
        <div class="stat-card" v-for="i in 4" :key="i">
          <el-skeleton animated>
            <template #template>
              <div class="stat-content">
                <el-skeleton-item variant="text" style="width: 60%; margin-bottom: 8px;" />
                <el-skeleton-item variant="h1" style="width: 40%;" />
              </div>
            </template>
          </el-skeleton>
        </div>
      </template>
      <template v-else>
        <div class="stat-card" v-for="stat in statsCards" :key="stat.key">
          <div class="stat-content">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value">
              {{ stat.value }}
              <span v-if="stat.suffix" class="stat-suffix">{{ stat.suffix }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 主要内容区 -->
    <div class="content-grid">
      <!-- 最近任务 -->
      <div class="content-card tasks-card">
        <div class="card-header">
          <h3 class="card-title">最近任务</h3>
          <router-link to="/detection" class="card-action">查看全部</router-link>
        </div>
        <div class="card-body">
          <template v-if="loading">
            <el-skeleton :rows="5" animated />
          </template>
          <template v-else>
            <div v-if="recentTasks.length === 0" class="empty-state">
              <p>暂无任务</p>
            </div>
            <div v-else class="task-list">
              <div v-for="task in recentTasks.slice(0, 5)" :key="task.task_id" class="task-item">
                <div class="task-info">
                  <div class="task-title">{{ task.task_id }}</div>
                  <div class="task-meta">
                    <span class="task-model">{{ task.model_id }}</span>
                    <span class="task-separator">·</span>
                    <span class="task-dataset">{{ task.dataset_id }}</span>
                  </div>
                </div>
                <div class="task-status">
                  <span class="status-badge" :class="`status-${task.status}`">
                    {{ getTaskStatusText(task.status) }}
                  </span>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 系统状态 -->
      <div class="content-card status-card">
        <div class="card-header">
          <h3 class="card-title">系统状态</h3>
        </div>
        <div class="card-body">
          <template v-if="loading">
            <el-skeleton :rows="4" animated />
          </template>
          <template v-else>
            <div class="status-item">
              <div class="status-label">系统状态</div>
              <div class="status-value">
                <span class="status-indicator" :class="getStatusClass(systemStatus)"></span>
                {{ getSystemStatusText(systemStatus) }}
              </div>
            </div>
            <div class="status-item">
              <div class="status-label">运行任务</div>
              <div class="status-value">{{ runningCount }} 个</div>
            </div>
            <div class="status-item">
              <div class="status-label">待处理任务</div>
              <div class="status-value">{{ pendingCount }} 个</div>
            </div>
            <div class="status-item">
              <div class="status-label">今日完成</div>
              <div class="status-value">{{ completedToday }} 个</div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </PageLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import PageLayout from '../components/common/PageLayout.vue'
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

// 统计卡片数据
const statsCards = computed(() => [
  {
    key: 'total',
    label: '检测样本总数',
    value: stats.value.totalSamples
  },
  {
    key: 'compliant',
    label: '合规样本',
    value: stats.value.compliantSamples
  },
  {
    key: 'non-compliant',
    label: '违规样本',
    value: stats.value.nonCompliantSamples
  },
  {
    key: 'rate',
    label: '合规率',
    value: stats.value.complianceRate.toFixed(1),
    suffix: '%'
  }
])

const getSystemStatusText = (status) => {
  const map = {
    idle: '空闲',
    detecting: '检测中',
    generating_report: '生成报告中',
    configuring: '配置管理中',
    error: '异常',
    unknown: '未知'
  }
  return map[status] || status
}

const getStatusClass = (status) => {
  if (status === 'error' || status === 'unknown') return ''
  return 'online'
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
  } catch {
    systemStatus.value = 'unknown'
  }

  try {
    const progressRes = await getProgress()
    if (progressRes.success && progressRes.queue) {
      const queue = progressRes.queue
      recentTasks.value = queue.slice(0, 10)
      runningCount.value = queue.filter(t => t.status === 'running').length
      pendingCount.value = queue.filter(t => t.status === 'pending').length
      completedToday.value = queue.filter(t => t.status === 'completed').length
    }
  } catch {
    // 使用默认值
  }

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
  } catch {
    // 使用默认值
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--spacing-5);
  margin-bottom: var(--spacing-6);
}

.stat-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--spacing-5);
  display: flex;
  gap: var(--spacing-4);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
  border: 1px solid var(--color-border);
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.stat-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  line-height: 1.2;
  margin-bottom: var(--spacing-1);
}

.stat-suffix {
  font-size: var(--font-size-xl);
  color: var(--color-text-secondary);
  margin-left: var(--spacing-1);
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.stat-trend.up {
  color: var(--color-success);
}

.stat-trend.down {
  color: var(--color-danger);
}

.stat-trend svg {
  width: 14px;
  height: 14px;
}

/* 内容网格 */
.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-5);
}

.content-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin: 0;
}

.card-action {
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  text-decoration: none;
  font-weight: var(--font-weight-medium);
  transition: color var(--transition-fast);
}

.card-action:hover {
  color: var(--color-primary-light);
}

.card-body {
  padding: var(--spacing-5);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-10) var(--spacing-5);
  color: var(--color-text-tertiary);
}

.empty-state svg {
  width: 64px;
  height: 64px;
  margin-bottom: var(--spacing-4);
  opacity: 0.5;
}

.empty-state p {
  font-size: var(--font-size-sm);
  margin: 0;
}

/* 任务列表 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3);
  border-radius: var(--radius-base);
  background: var(--color-bg);
  transition: all var(--transition-fast);
}

.task-item:hover {
  background: var(--color-surface-hover);
}

.task-info {
  flex: 1;
  min-width: 0;
}

.task-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  margin-bottom: var(--spacing-1);
  font-family: var(--font-family-mono);
}

.task-meta {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.task-separator {
  color: var(--color-text-tertiary);
}

.task-status {
  flex-shrink: 0;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  border-radius: var(--radius-full);
}

.status-badge.status-completed {
  background: var(--color-success-light);
  color: var(--color-success-dark);
}

.status-badge.status-running {
  background: var(--color-info-light);
  color: var(--color-info-dark);
}

.status-badge.status-pending {
  background: var(--color-gray-200);
  color: var(--color-gray-700);
}

.status-badge.status-failed {
  background: var(--color-danger-light);
  color: var(--color-danger-dark);
}

/* 系统状态 */
.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3) 0;
  border-bottom: 1px solid var(--color-border);
}

.status-item:last-child {
  border-bottom: none;
}

.status-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.status-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-gray-400);
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.status-indicator.online {
  background: var(--color-success);
}

/* 响应式 */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
