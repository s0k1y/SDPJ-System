<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">检测报告</h1>
      <p class="page-info">查看和管理所有安全检测生成的合规性报告</p>
      <ReportTable
        ref="tableRef"
        @view="handleView"
        @viewGroup="handleViewGroup"
        @download="handleDownload"
        @downloadAll="handleDownloadAll"
        @delete="handleDelete"
      />
    </div>

    <el-dialog v-model="detailVisible" title="报告详情" width="900px" destroy-on-close>
        <ReportChart v-if="detailVisible" :target-id="currentTargetId" :granularity="currentGranularity" />
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ReportTable from '../components/report/ReportTable.vue'
import ReportChart from '../components/report/ReportChart.vue'
import { exportReport, deleteReport } from '../api/report'

const tableRef = ref(null)
const detailVisible = ref(false)
const detailLoading = ref(false)
const currentTargetId = ref('')
const currentGranularity = ref('task_group')

const handleView = (report) => {
  currentTargetId.value = report.task_id
  currentGranularity.value = 'task'
  detailVisible.value = true
}

const handleViewGroup = (report) => {
  currentTargetId.value = report.task_group_id
  currentGranularity.value = 'task_group'
  detailVisible.value = true
}

const handleDownload = async (report) => {
  const reportId = report.task_group_id
  const taskId = report.task_id || null
  try {
    const blob = await exportReport(reportId, 'jsonl', taskId)
    if (!blob || blob.size === 0) {
      ElMessage.warning('报告暂无数据，无法导出')
      return
    }
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.download = `report_${report.task_id || reportId}.jsonl`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch {
    ElMessage.error('下载失败')
  }
}

const handleDownloadAll = async (report) => {
  const groupId = report.task_group_id
  try {
    const blob = await exportReport(groupId, 'jsonl')
    if (!blob || blob.size === 0) {
      ElMessage.warning('报告暂无数据，无法导出')
      return
    }
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.download = `report_${groupId}_all.jsonl`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('全部导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

const handleDelete = async (report) => {
  const isGroup = !report.task_id && !!report.task_group_id
  const targetId = isGroup ? report.task_group_id : (report.report_id || report.task_id)
  const granularity = isGroup ? 'task_group' : 'report'
  try {
    const msg = isGroup ? '确认删除该任务组的所有报告？删除后不可恢复。' : '确认删除该报告？删除后不可恢复。'
    await ElMessageBox.confirm(msg, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    const res = await deleteReport(targetId, granularity)
    if (res.success === false) {
      ElMessage.error(res.message || '删除失败')
      return
    }
    ElMessage.success('已删除')
    tableRef.value?.fetchReports()
  } catch {
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.page-container {
  width: 100%;
}

.page-inner {
  max-width: 936px;
  margin: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #404040;
  line-height: 32px;
  margin: 0 0 32px;
}

.page-info {
  font-size: 14px;
  color: #404040;
  line-height: 25px;
  margin: 0 0 22px;
}
</style>
