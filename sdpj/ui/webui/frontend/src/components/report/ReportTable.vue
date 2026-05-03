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

    <el-table :data="reports" style="width: 100%" v-loading="loading">
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
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getReportList } from '../../api/report'

const props = defineProps({
  userId: { type: String, default: '' },
  modelId: { type: String, default: '' }
})

defineEmits(['view', 'export', 'delete'])

const reports = ref([])
const loading = ref(false)

const getRiskType = (level) => {
  const map = { '低': 'success', '中': 'warning', '高': 'danger' }
  return map[level] || 'info'
}

const refresh = async () => {
  loading.value = true
  try {
    const params = {}
    if (props.userId) params.user_id = props.userId
    if (props.modelId) params.model_id = props.modelId
    const res = await getReportList(params)
    reports.value = Array.isArray(res) ? res : (res.reports || [])
  } catch {
    reports.value = []
  } finally {
    loading.value = false
  }
}

onMounted(refresh)

defineExpose({ refresh })
</script>
