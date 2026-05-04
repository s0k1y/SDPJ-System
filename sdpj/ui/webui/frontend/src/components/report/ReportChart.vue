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
      <!-- 统计概览 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-statistic title="总体合规率" :value="chartData.overall_rate || 0" suffix="%" :precision="1" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="合规样本" :value="chartData.compliant_count || 0" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="违规样本" :value="chartData.non_compliant_count || 0" />
        </el-col>
        <el-col :span="6" v-if="chartData.avg_iteration_count != null">
          <el-statistic title="平均迭代次数" :value="chartData.avg_iteration_count" :precision="2" />
        </el-col>
      </el-row>

      <el-divider />

      <!-- 图表区域 -->
      <el-row :gutter="20">
        <!-- 风险等级分布饼图 -->
        <el-col :xs="24" :sm="12" :md="8">
          <div class="chart-title">风险等级分布</div>
          <div ref="riskPieChart" class="chart-container"></div>
        </el-col>

        <!-- 各子类型合规率条形图 -->
        <el-col :xs="24" :sm="12" :md="16">
          <div class="chart-title">各子类型合规率对比</div>
          <div ref="subtypeBarChart" class="chart-container"></div>
        </el-col>
      </el-row>

      <el-divider />

      <!-- 详细数据表格 -->
      <div class="chart-title">详细数据</div>
      <el-table :data="subtypeItems" style="width: 100%" size="small">
        <el-table-column prop="category" label="风险子类型" />
        <el-table-column prop="total" label="总数" width="80" align="right" />
        <el-table-column prop="passed" label="合规" width="80" align="right" />
        <el-table-column prop="failed" label="违规" width="80" align="right" />
        <el-table-column prop="rate" label="合规率" width="120">
          <template #default="{ row }">
            <span :style="{ color: getProgressColor(row.rate) }">{{ row.rate.toFixed(1) }}%</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getVisualization } from '../../api/report'

const props = defineProps({
  taskGroupId: { type: String, default: '' }
})

const loading = ref(false)
const chartData = ref(null)
const riskPieChart = ref(null)
const subtypeBarChart = ref(null)

let riskPieInstance = null
let subtypeBarInstance = null

const getProgressColor = (rate) => {
  if (rate >= 80) return '#67c23a'
  if (rate >= 60) return '#e6a23c'
  return '#f56c6c'
}

const subtypeItems = computed(() => {
  if (!chartData.value) return []
  return chartData.value.subtype_compliance || []
})

// 初始化风险等级分布饼图
const initRiskPieChart = () => {
  if (!riskPieChart.value || !chartData.value?.risk_distribution?.data) return

  if (riskPieInstance) {
    riskPieInstance.dispose()
  }

  riskPieInstance = echarts.init(riskPieChart.value)

  const dist = chartData.value.risk_distribution.data
  const pieData = [
    { value: dist.low || 0, name: '低风险', itemStyle: { color: '#67c23a' } },
    { value: dist.medium || 0, name: '中风险', itemStyle: { color: '#e6a23c' } },
    { value: dist.high || 0, name: '高风险', itemStyle: { color: '#f56c6c' } }
  ]

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'center'
    },
    series: [
      {
        name: '风险等级',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: pieData
      }
    ]
  }

  riskPieInstance.setOption(option)
}

// 初始化子类型合规率条形图
const initSubtypeBarChart = () => {
  if (!subtypeBarChart.value || !subtypeItems.value.length) return

  if (subtypeBarInstance) {
    subtypeBarInstance.dispose()
  }

  subtypeBarInstance = echarts.init(subtypeBarChart.value)

  const categories = subtypeItems.value.map(item => item.category)
  const rates = subtypeItems.value.map(item => item.rate)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params) => {
        const item = params[0]
        return `${item.name}<br/>合规率: ${item.value.toFixed(1)}%`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    yAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        interval: 0,
        fontSize: 12
      }
    },
    series: [
      {
        name: '合规率',
        type: 'bar',
        data: rates.map(rate => ({
          value: rate,
          itemStyle: {
            color: getProgressColor(rate)
          }
        })),
        barWidth: '60%',
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%',
          fontSize: 12
        }
      }
    ]
  }

  subtypeBarInstance.setOption(option)
}

// 响应式调整图表大小
const handleResize = () => {
  riskPieInstance?.resize()
  subtypeBarInstance?.resize()
}

const fetchData = async () => {
  if (!props.taskGroupId) return
  loading.value = true
  try {
    const res = await getVisualization(props.taskGroupId)
    if (res.success) {
      chartData.value = res.data
      await nextTick()
      initRiskPieChart()
      initSubtypeBarChart()
    }
  } catch (error) {
    console.error('获取可视化数据失败:', error)
    chartData.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.taskGroupId, fetchData, { immediate: true })

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  riskPieInstance?.dispose()
  subtypeBarInstance?.dispose()
})
</script>

<style scoped>
.chart-loading {
  padding: var(--spacing-5);
}

.stats-row {
  margin-bottom: var(--spacing-4);
}

.chart-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--spacing-3);
}

.chart-container {
  width: 100%;
  height: 300px;
  margin-bottom: var(--spacing-4);
}

/* 响应式 */
@media (max-width: 768px) {
  .chart-container {
    height: 250px;
  }
}
</style>
