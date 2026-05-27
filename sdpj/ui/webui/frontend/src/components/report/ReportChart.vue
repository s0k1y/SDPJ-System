<template>
  <div class="report-chart">
    <div v-if="loading" class="loading-state">加载中...</div>
    <el-empty v-else-if="!chartData" description="暂无可视化数据" />
    <div v-else class="chart-content">
      <div class="stats-row">
        <div class="stat-item">
          <span class="stat-label">总体合规率</span>
          <span class="stat-number">{{ (chartData.overall_rate || 0).toFixed(1) }}<span class="stat-unit">%</span></span>
        </div>
        <div class="stat-item">
          <span class="stat-label">合规样本</span>
          <span class="stat-number">{{ chartData.statistics?.compliant || 0 }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">违规样本</span>
          <span class="stat-number">{{ chartData.statistics?.non_compliant || 0 }}</span>
        </div>
        <div class="stat-item" v-if="chartData.avg_iteration_count != null">
          <span class="stat-label">平均迭代次数</span>
          <span class="stat-number">{{ chartData.avg_iteration_count.toFixed(2) }}</span>
        </div>
      </div>

      <div class="section" v-if="taskDetails.length > 0">
        <h3 class="section-title">任务明细</h3>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th style="width: 20%">攻击路径</th>
                <th style="width: 20%">总数</th>
                <th style="width: 20%">合规</th>
                <th style="width: 20%">违规</th>
                <th style="width: 20%">合规率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="td in taskDetails" :key="td.attack_path">
                <td>{{ td.attack_path || '-' }}</td>
                <td>{{ td.total }}</td>
                <td>{{ td.compliant }}</td>
                <td>{{ td.non_compliant }}</td>
                <td>
                  <span :style="{ color: getProgressColor(td.compliance_rate) }">
                    {{ td.compliance_rate.toFixed(1) }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="section">
        <h3 class="section-title">详细数据</h3>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th style="width: 35%">风险子类型</th>
                <th style="width: 15%">总数</th>
                <th style="width: 15%">合规</th>
                <th style="width: 15%">违规</th>
                <th style="width: 20%">合规率</th>
              </tr>
            </thead>
            <tbody v-if="subtypeItems.length > 0">
              <tr v-for="item in subtypeItems" :key="item.category">
                <td>{{ item.category }}</td>
                <td>{{ item.total }}</td>
                <td>{{ item.passed }}</td>
                <td>{{ item.failed }}</td>
                <td>
                  <span :style="{ color: getProgressColor(item.rate) }">
                    {{ item.rate.toFixed(1) }}%
                  </span>
                </td>
              </tr>
            </tbody>
            <tbody v-else-if="!loading && subtypeItems.length === 0">
              <tr>
                <td colspan="99" class="empty-row"><div class="empty-center" style="margin-right: 16%;">暂无详细数据</div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getVisualization, getTaskVisualization } from '../../api/report'

const props = defineProps({
  targetId: { type: String, default: '' },
  granularity: { type: String, default: 'task_group' }
})

const chartData = ref(null)
const loading = ref(true)

const getProgressColor = (rate) => {
  if (rate >= 80) return '#22c55e'
  if (rate >= 60) return '#f59e0b'
  return '#ef4444'
}

const subtypeItems = computed(() => {
  if (!chartData.value) return []
  return chartData.value.subtype_compliance || []
})

const taskDetails = computed(() => {
  if (!chartData.value) return []
  return chartData.value.task_details || []
})

const fetchData = async () => {
  if (!props.targetId) return
  loading.value = true
  try {
    const res = props.granularity === 'task'
      ? await getTaskVisualization(props.targetId)
      : await getVisualization(props.targetId)
    if (res.success) {
      chartData.value = res.data?.data
      loading.value = false
      return
    }
  } catch {
    chartData.value = null
  }
  loading.value = false
}

watch(() => [props.targetId, props.granularity], fetchData, { immediate: true })
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px 32px;
  margin-bottom: 42px;
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

.stat-number {
  font-size: 28px;
  color: #404040;
  line-height: 36px;
}

.stat-unit {
  font-size: 18px;
  color: #8b8b8b;
}

.stat-text {
  font-size: 16px;
  line-height: 1.4;
  word-break: break-all;
}

.section {
  margin-bottom: 42px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #404040;
  margin: 0 0 21px;
}

.table-wrapper {
  background: #fafafa;
  border-radius: 10px;
  padding: 2px 14px 4px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  border-top: 2px solid #333333;
  border-bottom: 2px solid #333333;
}

th {
  color: #333333;
  font-weight: 600;
  font-size: 14px;
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid #333333;
}

td {
  color: #404040;
  font-size: 14px;
  padding: 10px 8px;
  vertical-align: middle;
  border: none;
}

.empty-row {
  padding: 24px 8px;
  color: #8b8b8b;
  font-size: 13px;
}

.loading-state {
  text-align: center;
  padding: 60px 0;
  font-size: 14px;
  color: #8b8b8b;
}

.empty-center {
  text-align: center;
}

@media (max-width: 768px) {
  .stats-row { grid-template-columns: 1fr 1fr; }
}
</style>
