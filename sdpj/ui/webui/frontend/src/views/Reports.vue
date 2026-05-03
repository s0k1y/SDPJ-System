<template>
  <div class="reports">
    <h2>检测报告</h2>

    <ReportTable
      ref="tableRef"
      @view="handleView"
      @export="handleExport"
      @delete="handleDelete"
    />

    <el-dialog v-model="chartVisible" title="报告详情" width="80%" destroy-on-close>
      <ReportChart :task-group-id="selectedTaskGroupId" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteReport, exportReport } from '../api/report'
import ReportTable from '../components/report/ReportTable.vue'
import ReportChart from '../components/report/ReportChart.vue'

const tableRef = ref()
const chartVisible = ref(false)
const selectedTaskGroupId = ref('')

const handleView = (row) => {
  selectedTaskGroupId.value = row.task_group_id
  chartVisible.value = true
}

const handleExport = async (row) => {
  try {
    const res = await exportReport(row.task_group_id, 'pdf')
    if (res.success) {
      ElMessage.success('报告导出成功')
    }
  } catch {
    ElMessage.error('导出失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该报告吗？', '确认删除', {
      type: 'warning'
    })
    const res = await deleteReport(row.task_group_id, 'report')
    if (res || res?.success) {
      ElMessage.success('删除成功')
      tableRef.value?.refresh()
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.reports h2 {
  margin-bottom: 20px;
}
</style>
