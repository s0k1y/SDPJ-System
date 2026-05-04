<template>
  <el-card class="report-chart">
    <template #header>
      <span>检测结果可视化</span>
    </template>

    <div v-if="loading" class="chart-loading">
      <el-skeleton :rows="5" animated />
    </div>

    <el-empty v-else-if="!chartData" description="暂无可视化数据" />

    <div v-else class="chart-content">
      <el-row :gutter="20">
        <el-col :span="12">
          <h4>合规率概览</h4>
          <div class="chart-bars">
            <div class="bar-item">
              <span class="bar-label">总体合规率</span>
              <el-progress
                :percentage="chartData.overall_rate || 0"
                :color="'#409eff'"
                :stroke-width="18"
              />
            </div>
          </div>
          <div v-if="chartData.avg_iteration_count != null" class="iteration-stat">
            <el-statistic title="动态检测平均迭代次数" :value="chartData.avg_iteration_count" :precision="2" />
          </div>
        </el-col>
        <el-col :span="12">
          <h4>风险等级统计</h4>
          <div class="risk-stats">
            <div
              v-for="item in riskItems"
              :key="item.label"
              class="risk-item"
            >
              <el-statistic :title="item.label" :value="item.count">
                <template #suffix>
                  <el-tag :type="item.type" size="small">{{ item.label }}</el-tag>
                </template>
              </el-statistic>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-divider />

      <h4>各子类型合规率</h4>
      <el-table :data="subtypeItems" style="width: 100%" size="small">
        <el-table-column prop="category" label="风险子类型" />
        <el-table-column prop="total" label="总数" width="80" />
        <el-table-column prop="passed" label="合规" width="80" />
        <el-table-column prop="failed" label="违规" width="80" />
        <el-table-column prop="rate" label="合规率" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.rate"
              :stroke-width="6"
              :color="row.rate >= 80 ? '#67c23a' : row.rate >= 60 ? '#e6a23c' : '#f56c6c'"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getVisualization } from '../../api/report'

const props = defineProps({
  taskGroupId: { type: String, default: '' }
})

const loading = ref(false)
const chartData = ref(null)

const riskItems = computed(() => {
  if (!chartData.value) return []
  const dist = chartData.value.risk_distribution
  if (!dist || !dist.data) return []
  const counts = { '低风险': 0, '中风险': 0, '高风险': 0 }
  const stats = chartData.value.statistics
  if (stats) {
    const rate = stats.compliance_rate
    if (rate >= 90) counts['低风险'] = stats.total
    else if (rate >= 70) counts['中风险'] = stats.total
    else counts['高风险'] = stats.total
  }
  return [
    { label: '低风险', count: counts['低风险'], type: 'success' },
    { label: '中风险', count: counts['中风险'], type: 'warning' },
    { label: '高风险', count: counts['高风险'], type: 'danger' }
  ]
})

const subtypeItems = computed(() => {
  if (!chartData.value) return []
  return chartData.value.subtype_compliance || []
})

const fetchData = async () => {
  if (!props.taskGroupId) return
  loading.value = true
  try {
    const res = await getVisualization(props.taskGroupId)
    if (res.success) {
      chartData.value = res.data
    }
  } catch {
    chartData.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.taskGroupId, fetchData, { immediate: true })
</script>

<style scoped>
.chart-loading {
  padding: 20px;
}

.chart-bars {
  padding: 10px 0;
}

.bar-item {
  margin-bottom: 16px;
}

.bar-label {
  display: block;
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.risk-stats {
  display: flex;
  gap: 24px;
  padding: 10px 0;
}

.iteration-stat {
  margin-top: 20px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

h4 {
  margin-bottom: 12px;
  color: #303133;
}
</style>
