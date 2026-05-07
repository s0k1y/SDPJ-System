<template>
  <div class="report-chart">
    <el-empty v-if="!loading && !chartData" description="暂无可视化数据" />

    <div v-else class="chart-content">
      <div class="stats-row">
        <div class="stat-item">
          <span class="stat-label">总体合规率</span>
          <span class="stat-number">{{ (chartData.overall_rate || 0).toFixed(1) }}<span class="stat-unit">%</span></span>
        </div>
        <div class="stat-item">
          <span class="stat-label">合规样本</span>
          <span class="stat-number">{{ chartData.compliant_count || 0 }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">违规样本</span>
          <span class="stat-number">{{ chartData.non_compliant_count || 0 }}</span>
        </div>
        <div class="stat-item" v-if="chartData.avg_iteration_count != null">
          <span class="stat-label">平均迭代次数</span>
          <span class="stat-number">{{ chartData.avg_iteration_count.toFixed(2) }}</span>
        </div>
      </div>

      <div class="section">
        <div class="chart-row">
          <div class="chart-col">
            <h3 class="section-title">风险等级分布</h3>
            <div ref="riskPieChart" class="chart-box"></div>
          </div>
          <div class="chart-col chart-col-wide">
            <h3 class="section-title">各子类型合规率对比</h3>
            <div ref="subtypeBarChart" class="chart-box"></div>
          </div>
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
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  PieChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  CanvasRenderer
])
import { getVisualization, getTaskVisualization } from '../../api/report'

const props = defineProps({
  targetId: { type: String, default: '' },
  granularity: { type: String, default: 'task_group' }
})

const chartData = ref(null)
const loading = ref(true)
const riskPieChart = ref(null)
const subtypeBarChart = ref(null)

let riskPieInstance = null
let subtypeBarInstance = null

const getProgressColor = (rate) => {
  if (rate >= 80) return '#22c55e'
  if (rate >= 60) return '#f59e0b'
  return '#ef4444'
}

const subtypeItems = computed(() => {
  if (!chartData.value) return []
  return chartData.value.subtype_compliance || []
})

const initRiskPieChart = () => {
  if (!riskPieChart.value || !chartData.value?.risk_distribution?.data) return
  if (riskPieInstance) riskPieInstance.dispose()
  riskPieInstance = echarts.init(riskPieChart.value)

  const dist = chartData.value.risk_distribution.data
  const pieData = [
    { value: dist.low || 0, name: '低风险', itemStyle: { color: '#22c55e' } },
    { value: dist.medium || 0, name: '中风险', itemStyle: { color: '#f59e0b' } },
    { value: dist.high || 0, name: '高风险', itemStyle: { color: '#ef4444' } }
  ]

  riskPieInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left', top: 'center' },
    series: [{
      name: '风险等级', type: 'pie', radius: ['40%', '70%'], center: ['60%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%' },
      emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
      data: pieData
    }]
  })
}

const initSubtypeBarChart = () => {
  if (!subtypeBarChart.value || !subtypeItems.value.length) return
  if (subtypeBarInstance) subtypeBarInstance.dispose()
  subtypeBarInstance = echarts.init(subtypeBarChart.value)

  const categories = subtypeItems.value.map(item => item.category)
  const rates = subtypeItems.value.map(item => item.rate)

  subtypeBarInstance.setOption({
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: (params) => `${params[0].name}<br/>合规率: ${params[0].value.toFixed(1)}%`
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    yAxis: { type: 'category', data: categories, axisLabel: { interval: 0, fontSize: 12 } },
    series: [{
      name: '合规率', type: 'bar',
      data: rates.map(rate => ({ value: rate, itemStyle: { color: getProgressColor(rate) } })),
      barWidth: '60%',
      label: { show: true, position: 'right', formatter: '{c}%', fontSize: 12 }
    }]
  })
}

let resizeTimer = null
const handleResize = () => {
  if (resizeTimer) return
  resizeTimer = setTimeout(() => {
    riskPieInstance?.resize()
    subtypeBarInstance?.resize()
    resizeTimer = null
  }, 200)
}

const fetchData = async () => {
  if (!props.targetId) return
  loading.value = true
  try {
    const res = props.granularity === 'task'
      ? await getTaskVisualization(props.targetId)
      : await getVisualization(props.targetId)
    if (res.success) {
      chartData.value = res.data?.data
      await nextTick()
      initRiskPieChart()
      initSubtypeBarChart()
    }
  } catch {
    chartData.value = null
  } finally {
    loading.value = false
  }
}

watch(() => [props.targetId, props.granularity], fetchData, { immediate: true })

onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeTimer) clearTimeout(resizeTimer)
  riskPieInstance?.dispose()
  subtypeBarInstance?.dispose()
})
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

.section {
  margin-bottom: 42px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #404040;
  margin: 0 0 21px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 32px;
}

.chart-box {
  width: 100%;
  height: 300px;
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
}

th {
  color: #8b8b8b;
  font-weight: 600;
  font-size: 14px;
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid #e5e5e5;
}

td {
  color: #404040;
  font-size: 14px;
  padding: 10px 8px;
  vertical-align: middle;
}

.empty-row {
  padding: 24px 8px;
  color: #8b8b8b;
  font-size: 13px;
}

.empty-center {
  text-align: center;
}

@media (max-width: 768px) {
  .stats-row { grid-template-columns: 1fr 1fr; }
  .chart-row { grid-template-columns: 1fr; }
  .chart-box { height: 250px; }
}
</style>
