<template>
  <el-card class="report-table">
    <template #header>
      <div class="card-header">
        <span>报告列表</span>
        <div>
          <el-button size="small" @click="refresh" :loading="loading">刷新</el-button>
        </div>
      </div>
    </template>

    <el-table :data="paginatedReports" style="width: 100%" v-loading="loading">
      <el-table-column prop="task_group_id" label="任务组ID" width="180" />
      <el-table-column prop="model_id" label="模型" width="140" />
      <el-table-column prop="detection_type" label="检测类型" width="120">
        <template #default="{ row }">
          <el-tag size="small">{{ row.detection_type || '-' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="risk_level" label="风险等级" width="100">
        <template #default="{ row }">
          <el-tag :type="getRiskType(row.risk_level)" size="small">
            {{ row.risk_level || '-' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="compliance_rate" label="合规率" width="100" />
      <el-table-column prop="created_at" label="生成时间" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="$emit('view', row)">查看</el-button>
          <el-button size="small" type="primary" @click="$emit('export', row)">
            导出
          </el-button>
          <el-button size="small" type="danger" @click="$emit('delete', row)">
            删除
          </el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty v-if="!loading" description="暂无报告数据" />
      </template>
    </el-table>

    <div class="pagination-wrapper" v-if="reports.length > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="reports.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getReportList } from '../../api/report'

const props = defineProps({
  userId: { type: String, default: '' },
  modelId: { type: String, default: '' }
})

defineEmits(['view', 'export', 'delete'])

const reports = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)

const paginatedReports = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return reports.value.slice(start, end)
})

const getRiskType = (level) => {
  const map = { '低': 'success', '中': 'warning', '高': 'danger' }
  return map[level] || 'info'
}

const handleSizeChange = () => {
  currentPage.value = 1
}

const handleCurrentChange = () => {
  // 页码变化时自动滚动到表格顶部
  document.querySelector('.report-table')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const refresh = async () => {
  loading.value = true
  try {
    const params = {}
    if (props.userId) params.user_id = props.userId
    if (props.modelId) params.model_id = props.modelId
    const res = await getReportList(params)
    reports.value = Array.isArray(res) ? res : (res.reports || [])
    currentPage.value = 1
  } catch {
    reports.value = []
  } finally {
    loading.value = false
  }
}

onMounted(refresh)

defineExpose({ refresh })
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-wrapper {
  margin-top: var(--spacing-4);
  display: flex;
  justify-content: flex-end;
}
</style>
