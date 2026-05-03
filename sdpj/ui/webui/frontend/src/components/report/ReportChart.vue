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
          <h4>合规率分布</h4>
          <div class="chart-bars">
            <div
              v-for="item in complianceItems"
              :key="item.label"
              class="bar-item"
            >
              <span class="bar-label">{{ item.label }}</span>
              <el-progress
                :percentage="item.value"
                :color="item.color"
                :stroke-width="18"
              />
            </div>
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

      <h4>检测详情</h4>
      <el-table :data="detailItems" style="width: 100%" size="small">
        <el-table-column prop="category" label="检测类别" />
        <el-table-column prop="total" label="总数" width="80" />
        <el-table-column prop="passed" label="通过" width="80" />
        <el-table-column prop="failed" label="未通过" width="80" />
        <el-table-column prop="rate" label="合规率" width="100">
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

const complianceItems = computed(() => {
  if (!chartData.value) return []
  const data = chartData.value
  return [
    { label: '总体合规率', value: data.overall_rate || 0, color: '#409eff' },
    { label: '安全性', value: data.safety_rate || 0, color: '#67c23a' },
    { label: '公平性', value: data.fairness_rate || 0, color: '#e6a23c' },
    { label: '隐私保护', value: data.privacy_rate || 0, color: '#f56c6c' }
  ]
})

const riskItems = computed(() => {
  if (!chartData.value) return []
  const risk = chartData.value.risk_distribution || {}
  return [
    { label: '低风险', count: risk.low || 0, type: 'success' },
    { label: '中风险', count: risk.medium || 0, type: 'warning' },
    { label: '高风险', count: risk.high || 0, type: 'danger' }
  ]
})

const detailItems = computed(() => {
  if (!chartData.value) return []
  return chartData.value.details || []
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

h4 {
  margin-bottom: 12px;
  color: #303133;
}
</style>
