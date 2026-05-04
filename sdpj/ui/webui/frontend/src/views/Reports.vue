<template>
  <PageLayout title="检测报告" description="查看和管理大模型安全检测报告">
    <ReportTable
      ref="tableRef"
      @view="handleView"
      @export="handleExport"
      @delete="handleDelete"
    />

    <el-dialog v-model="chartVisible" title="报告详情" width="80%" destroy-on-close>
      <ReportChart :task-group-id="selectedTaskGroupId" />
    </el-dialog>
  </PageLayout>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteReport, exportReport } from '../api/report'
import PageLayout from '../components/common/PageLayout.vue'
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
    const blob = await exportReport(row.task_group_id)

    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report_${row.task_group_id}_${Date.now()}.jsonl`
    document.body.appendChild(link)
    link.click()

    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('报告导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该报告吗？', '确认删除', {
      type: 'warning'
    })
    const res = await deleteReport(row.task_group_id, 'report')
    if (res?.success) {
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
/* 无需额外样式，由 PageLayout 统一管理 */
</style>
