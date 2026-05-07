<template>
  <div class="report-table">
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th style="width: 18%">任务组ID / 任务ID</th>
            <th style="width: 12%">模型</th>
            <th style="width: 12%">数据集</th>
            <th style="width: 10%">合规率</th>
            <th style="width: 10%">风险等级</th>
            <th style="width: 10%">状态</th>
            <th style="width: 28%">操作</th>
          </tr>
        </thead>
        <template v-if="!loading && flattenedRows.length > 0">
          <template v-for="row in flattenedRows" :key="row.id">
            <tr :class="{ 'group-row': !row.isLeaf, 'task-row': row.isLeaf }">
              <td>
                <div class="name-cell" :style="{ paddingLeft: (row.level * 20) + 'px' }">
                  <span v-if="!row.isLeaf" class="folder-icon" @click="toggleExpand(row)">
                    {{ row.expanded ? '▼' : '▶' }}
                  </span>
                  <span v-else class="file-icon">📄</span>
                  <span class="cell-mono name-text">{{ row.label }}</span>
                </div>
              </td>
              <td>
                <span v-if="!row.isLeaf" class="cell-mono">{{ row.model_id || '-' }}</span>
              </td>
              <td>
                <span v-if="row.isLeaf" class="cell-mono">{{ row.dataset_name || '-' }}</span>
              </td>
              <td>
                <span v-if="row.isLeaf">{{ row.compliance_rate != null ? row.compliance_rate.toFixed(1) + '%' : '-' }}</span>
                <span v-else class="folder-summary">{{ row.compliance_rate != null ? row.compliance_rate.toFixed(1) + '%' : '-' }}</span>
              </td>
              <td>
                <span :class="riskClass(row.risk_level)">{{ row.risk_level || '-' }}</span>
              </td>
              <td>
                <span class="status-tag" :class="`tag-${row.status || 'unknown'}`">
                  {{ statusText(row.status) }}
                </span>
              </td>
              <td>
                <div class="action-btns" v-if="row.isLeaf">
                  <el-button class="action-btn" size="small" @click="$emit('view', row.raw)">查看</el-button>
                  <el-button class="action-btn" size="small" @click="$emit('download', row.raw)">导出</el-button>
                  <el-button class="action-btn action-btn-danger" size="small" @click="$emit('delete', row.raw)">删除</el-button>
                </div>
                <div class="action-btns" v-else-if="!row.isLeaf">
                  <el-button class="action-btn" size="small" @click="$emit('viewGroup', row.raw)">查看</el-button>
                  <el-button class="action-btn" size="small" @click="$emit('downloadAll', row.raw)">全部导出</el-button>
                  <el-button class="action-btn action-btn-danger" size="small" @click="$emit('delete', row.raw)">删除</el-button>
                </div>
              </td>
            </tr>
          </template>
        </template>
        <tbody v-else-if="flattenedRows.length === 0">
          <tr>
            <td colspan="99" class="empty-row"><div class="empty-center" style="margin-right: 26%;">暂无检测报告</div></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getReportList } from '../../api/report'

const emit = defineEmits(['view', 'viewGroup', 'download', 'downloadAll', 'delete'])

const groups = ref([])
const loading = ref(true)
const expandedMap = ref({})

const statusText = (status) => {
  const map = { completed: '已完成', generating: '生成中', failed: '失败' }
  return map[status] || status || '未知'
}

const riskClass = (level) => {
  if (!level || level === 'N/A') return 'risk-na'
  if (level === '低风险') return 'risk-low'
  if (level === '中风险') return 'risk-mid'
  return 'risk-high'
}

const buildFlattenedRows = (groups) => {
  const result = []
  groups.forEach(group => {
    const tgId = group.task_group_id
    const isExpanded = expandedMap.value[tgId] !== false
    result.push({
      id: tgId,
      isLeaf: false,
      level: 0,
      expanded: isExpanded,
      label: tgId,
      model_id: group.model_id,
      compliance_rate: group.compliance_rate,
      risk_level: group.risk_level,
      status: group.status,
      raw: group,
    })
    if (isExpanded && group.children) {
      group.children.forEach(child => {
        result.push({
          id: child.task_id,
          isLeaf: true,
          level: 1,
          label: child.task_id,
          dataset_name: child.dataset_name,
          compliance_rate: child.compliance_rate,
          risk_level: child.risk_level,
          status: child.status,
          report_id: child.report_id,
          raw: { ...child, task_group_id: tgId },
        })
      })
    }
  })
  return result
}

const flattenedRows = computed(() => buildFlattenedRows(groups.value))

const toggleExpand = (row) => {
  expandedMap.value[row.id] = !expandedMap.value[row.id]
  expandedMap.value = { ...expandedMap.value }
}

const fetchReports = async () => {
  loading.value = true
  try {
    const res = await getReportList()
    if (res.success) {
      groups.value = res.data || []
    }
  } catch { /* keep defaults */ }
  finally { loading.value = false }
}

defineExpose({ fetchReports })

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
  white-space: nowrap;
}

.cell-mono {
  font-family: var(--font-family-mono);
  letter-spacing: 0.3px;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.name-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.folder-icon {
  cursor: pointer;
  user-select: none;
  color: #8b8b8b;
  font-size: 12px;
  width: 16px;
  display: inline-block;
  text-align: center;
}

.folder-icon:hover {
  color: #404040;
}

.file-icon {
  font-size: 14px;
  width: 16px;
  display: inline-block;
  text-align: center;
}

.folder-summary {
  color: #8b8b8b;
  font-size: 13px;
}

.group-row {
  background: #f5f5f5;
  font-weight: 500;
}

.task-row:hover {
  background: #f9f9f9;
}

.status-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  white-space: nowrap;
  display: inline-block;
}

.tag-completed {
  background: transparent;
  color: #16a34a;
}

.tag-generating {
  background: transparent;
  color: #2563eb;
}

.tag-failed {
  background: transparent;
  color: #dc2626;
}

.tag-unknown {
  background: #f5f5f5;
  color: #8b8b8b;
}

.risk-low {
  color: #16a34a;
  font-size: 13px;
}

.risk-mid {
  color: #f59e0b;
  font-size: 13px;
}

.risk-high {
  color: #dc2626;
  font-size: 13px;
}

.risk-na {
  color: #8b8b8b;
  font-size: 13px;
}

.action-btns {
  display: grid;
  grid-template-columns: 50px 70px 50px;
  gap: 8px;
  align-items: center;
}

.action-spacer {
  display: none;
}

.action-btn {
  height: 30px;
  padding: 0;
  font-size: 12px;
  border-radius: 10px;
  border: none !important;
  background: transparent !important;
  color: #404040 !important;
}

.action-btn:hover {
  background: #e5e5e5 !important;
  color: #404040 !important;
}

.action-btn-danger:hover {
  color: #dc2626 !important;
  background: rgba(239, 68, 68, 0.08) !important;
}

.empty-row {
  padding: 24px 8px;
  color: #8b8b8b;
  font-size: 13px;
}

.empty-center {
  text-align: center;
}
</style>
