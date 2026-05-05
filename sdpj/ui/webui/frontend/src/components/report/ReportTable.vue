<template>
  <div class="report-table">
    <div class="table-wrapper" v-loading="loading">
      <table>
        <thead>
          <tr>
            <th style="width: 25%">报告ID</th>
            <th style="width: 15%">任务ID</th>
            <th style="width: 10%">合规率</th>
            <th style="width: 20%">生成时间</th>
            <th style="width: 15%">状态</th>
            <th style="width: 15%">操作</th>
          </tr>
        </thead>
        <tbody v-if="reports.length > 0">
          <tr v-for="report in reports" :key="report.report_id">
            <td><span class="cell-mono">{{ report.report_id }}</span></td>
            <td><span class="cell-mono">{{ report.task_id || '-' }}</span></td>
            <td>{{ report.compliance_rate != null ? (report.compliance_rate * 100).toFixed(1) + '%' : '-' }}</td>
            <td>{{ report.generated_at || '-' }}</td>
            <td>
              <span class="status-tag" :class="`tag-${report.status || 'unknown'}`">
                {{ statusText(report.status) }}
              </span>
            </td>
            <td>
              <div class="action-btns">
                <el-button class="action-btn" size="small" @click="$emit('view', report)" v-if="report.report_id">查看</el-button>
                <el-button class="action-btn" size="small" @click="$emit('download', report)" v-if="report.report_id">下载</el-button>
                <el-button class="action-btn action-btn-danger" size="small" @click="$emit('delete', report)" v-if="report.report_id">删除</el-button>
              </div>
            </td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr>
            <td colspan="99" class="empty-row">暂无检测报告</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineEmits } from 'vue'
import { getReportList } from '../../api/report'

defineEmits(['view', 'download', 'delete'])

const reports = ref([])
const loading = ref(false)

const statusText = (status) => {
  const map = { completed: '已完成', generating: '生成中', failed: '失败' }
  return map[status] || status || '未知'
}

const fetchReports = async () => {
  loading.value = true
  try {
    const res = await getReportList()
    if (res.success) {
      reports.value = res.reports || []
    }
  } catch { /* keep defaults */ }
  finally { loading.value = false }
}

onMounted(fetchReports)
</script>

<style scoped>
.report-table {
  width: 100%;
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

.cell-mono {
  font-family: var(--font-family-mono);
  letter-spacing: 0.3px;
}

.status-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
}

.tag-completed {
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
}

.tag-generating {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
}

.tag-failed {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.tag-unknown {
  background: #f5f5f5;
  color: #8b8b8b;
}

.action-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  height: 30px;
  padding: 0 14px;
  font-size: 12px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #404040;
}

.action-btn:hover {
  background: #e5e5e5;
}

.action-btn-danger:hover {
  color: #dc2626;
  background: rgba(239, 68, 68, 0.08);
}

.empty-row {
  padding: 24px 8px;
  text-align: center;
  color: #8b8b8b;
  font-size: 13px;
}
</style>
