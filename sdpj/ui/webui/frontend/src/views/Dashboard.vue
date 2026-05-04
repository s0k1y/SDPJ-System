<template>
  <div class="dashboard">
    <h2>仪表盘</h2>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <el-statistic title="检测样本总数" :value="stats.totalSamples" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="合规样本" :value="stats.compliantSamples" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="违规样本" :value="stats.nonCompliantSamples" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="合规率" :value="stats.complianceRate" suffix="%" />
        </el-card>
      </el-col>
      <el-col v-if="stats.avgIterationCount != null" :span="6">
        <el-card>
          <el-statistic title="动态检测平均迭代次数" :value="stats.avgIterationCount" :precision="2" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>最近任务</template>
          <el-table :data="recentTasks" style="width: 100%" v-loading="loading">
            <el-table-column prop="task_id" label="任务ID" width="200" />
            <el-table-column prop="model_id" label="模型" />
            <el-table-column prop="dataset_id" label="数据集" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>系统状态</template>
          <el-descriptions :column="1" size="small">
            <el-descriptions-item label="系统状态">
              <el-tag :type="systemOnline ? 'success' : 'danger'">
                {{ systemOnline ? '在线' : '离线' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="运行任务">
              {{ runningCount }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { getProgress } from '../api/detection'
import { getComplianceStatistics } from '../api/report'

const loading = ref(false)
const systemOnline = ref(false)
const runningCount = ref(0)

const stats = ref({
  totalSamples: 0,
  compliantSamples: 0,
  nonCompliantSamples: 0,
  complianceRate: 0,
  avgIterationCount: null
})

const recentTasks = ref([])

const getStatusType = (status) => {
  const map = { completed: 'success', running: '', pending: 'info', failed: 'danger' }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = { completed: '已完成', running: '运行中', pending: '等待中', failed: '失败' }
  return map[status] || status
}

onMounted(async () => {
  loading.value = true
  try {
    const statusRes = await api.get('/status')
    systemOnline.value = statusRes?.status === 'ok' || statusRes?.status === 'running'
  } catch {
    systemOnline.value = false
  }

  try {
    const progressRes = await getProgress()
    if (progressRes.success && progressRes.queue) {
      const queue = progressRes.queue
      recentTasks.value = queue.slice(0, 10)
      runningCount.value = queue.filter(t => t.status === 'running').length
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
.dashboard h2 {
  margin-bottom: 20px;
}
</style>
