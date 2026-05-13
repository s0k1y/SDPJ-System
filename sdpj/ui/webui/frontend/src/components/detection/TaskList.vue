<template>
  <div class="task-list">
    <div class="section-header">
      <h2 class="section-title">任务队列</h2>
    </div>

    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th style="width: 35%">任务</th>
            <th style="width: 20%">状态</th>
            <th style="width: 25%">进度</th>
            <th style="width: 20%">操作</th>
          </tr>
        </thead>
        <tbody v-if="flatRows.length > 0">
          <template v-for="row in flatRows" :key="row.id">
            <tr :class="{ 'group-row': row.isGroup, 'child-row': !row.isGroup }">
              <td>
                <div class="name-cell" :style="{ paddingLeft: row.isGroup ? '0' : '28px' }">
                  <span v-if="row.isGroup" class="expand-icon" @click="toggleExpand(row)">
                    {{ row.expanded ? '&#9660;' : '&#9654;' }}
                  </span>
                  <div class="name-content">
                    <span class="name-text">{{ row.label }}</span>
                    <span class="id-hint">{{ row.shortId }}</span>
                  </div>
                </div>
              </td>
              <td>
                <el-tooltip
                  v-if="row.status === 'failed' && row.error_message"
                  placement="top"
                  :show-after="100"
                  effect="light"
                  :raw-content="true"
                >
                  <template #content>
                    <div class="error-tooltip" v-html="formatErrors(row.error_message)"></div>
                  </template>
                  <span class="status-tag" :class="`tag-${row.status}`">{{ getStatusText(row.status) }}</span>
                </el-tooltip>
                <span v-else class="status-tag" :class="`tag-${row.status}`">{{ getStatusText(row.status) }}</span>
              </td>
              <td>
                <template v-if="row.isGroup">
                  <div class="progress-info">
                    <div class="progress-bar-bg">
                      <div class="progress-bar-fill" :style="{ width: groupPercent(row) + '%' }" :class="groupBarClass(row)"></div>
                    </div>
                    <span class="status-tag" :class="`tag-${row.status}`">{{ getStatusText(row.status) }}</span>
                    <span v-if="row.etaText" class="eta-tag">{{ row.etaText }}</span>
                  </div>
                </template>
                <template v-else>
                  <div v-if="row.taskProgress" class="progress-info">
                    <div class="progress-bar-bg">
                      <div class="progress-bar-fill" :style="{ width: taskPercent(row) + '%' }" :class="taskBarClass(row)"></div>
                    </div>
                    <span class="progress-text">{{ row.taskProgress.processed }}/{{ row.taskProgress.total }}</span>
                  </div>
                  <span v-else class="status-tag" :class="`tag-${row.status}`">{{ getStatusText(row.status) }}</span>
                </template>
              </td>
              <td>
                <div class="action-btns">
                  <el-button
                    v-if="canCancel(row.status) && row.dataset_id !== 'poc_selecting' && row.dataset_id !== 'dynamic_detecting'"
                    class="action-btn action-btn-danger"
                    size="small"
                    @click="handleCancel(row)"
                  >取消</el-button>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
        <tbody v-else-if="loaded && flatRows.length === 0">
          <tr>
            <td colspan="99" class="empty-row"><div class="empty-center" style="margin-right: 16%;">暂无任务</div></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cancelTask } from '../../api/detection'

const props = defineProps({
  groups: { type: Array, default: () => [] }
})

const expandedIds = ref({})
const loaded = ref(false)

watch(() => props.groups, () => { loaded.value = true }, { immediate: true })

const getStatusText = (status) => {
  const map = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return map[status] || status
}

const formatErrors = (msg) => {
  if (!msg) return ''
  return msg.split('\n').map(line => `<div>${line}</div>`).join('')
}

const canCancel = (status) => {
  return status === 'pending' || status === 'running'
}

const formatEta = (seconds) => {
  if (seconds == null || seconds < 0) return '计算中...'
  if (seconds === 0) return ''
  if (seconds < 60) return `${Math.round(seconds)}秒`
  if (seconds < 3600) {
    const m = Math.floor(seconds / 60)
    const s = Math.round(seconds % 60)
    return `${m}分${s}秒`
  }
  const h = Math.floor(seconds / 3600)
  const m = Math.round((seconds % 3600) / 60)
  return `${h}小时${m}分`
}

const groupPercent = (row) => {
  if (!row.progress || row.progress.total === 0) return 0
  return Math.round((row.progress.completed / row.progress.total) * 100)
}

const groupBarClass = (row) => {
  if (row.status === 'failed') return 'bar-failed'
  if (row.status === 'completed') return 'bar-completed'
  return 'bar-running'
}

const taskPercent = (row) => {
  if (!row.taskProgress || row.taskProgress.total === 0) return 0
  return Math.round((row.taskProgress.processed / row.taskProgress.total) * 100)
}

const taskBarClass = (row) => {
  if (row.status === 'failed') return 'bar-failed'
  if (row.status === 'completed') return 'bar-completed'
  return 'bar-running'
}

const flatRows = computed(() => {
  const rows = []
  for (const g of props.groups) {
    const gid = g.task_group_id
    const expanded = expandedIds.value[gid] !== false
    const groupErrors = g.children
        .filter(c => c.status === 'failed' && c.error_message)
        .map(c => `${c.dataset_name}: ${c.error_message}`)
        .join('\n')
    rows.push({
      id: gid,
      isGroup: true,
      expanded,
      label: g.model_name,
      shortId: gid,
      status: g.status,
      progress: g.progress,
      task_group_id: gid,
      error_message: groupErrors || '',
      etaText: g.status === 'running' ? formatEta(g.eta_seconds) : '',
    })
    if (expanded) {
      for (const c of g.children) {
        rows.push({
          id: c.task_id,
          isGroup: false,
          label: c.dataset_name,
          shortId: c.task_id,
          status: c.status,
          task_id: c.task_id,
          dataset_id: c.dataset_id || '',
          error_message: c.error_message || '',
          taskProgress: c.progress || null,
        })
      }
    }
  }
  return rows
})

const toggleExpand = (row) => {
  const id = row.task_group_id
  const isExpanded = expandedIds.value[id] !== false
  expandedIds.value = { ...expandedIds.value, [id]: !isExpanded }
}

const handleCancel = async (row) => {
  const label = row.isGroup ? '任务组' : '任务'
  await ElMessageBox.confirm(`确认取消该${label}？`, '提示', { type: 'warning' })
  try {
    const params = row.isGroup
      ? { task_group_id: row.task_group_id }
      : { task_id: row.task_id }
    const res = await cancelTask(params)
    if (res.success) {
      ElMessage.success('已取消')
    } else {
      ElMessage.error(res.message || '取消失败')
    }
  } catch { ElMessage.error('取消失败') }
}
</script>

<style scoped>
.task-list {
  margin-top: 42px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 21px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #404040;
  margin: 0;
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
  color: #333333;
  font-weight: 600;
  font-size: 14px;
  text-align: left;
  padding: 10px 8px;
  border-top: 2px solid #333333;
  border-bottom: 1px solid #333333;
}

td {
  color: #404040;
  font-size: 14px;
  padding: 10px 8px;
  vertical-align: middle;
  border: none;
}

table tr:last-child td {
  border-bottom: 2px solid #333333;
}

.group-row {
  background: #f5f5f5;
  font-weight: 500;
}

.child-row:hover {
  background: #f9f9f9;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expand-icon {
  cursor: pointer;
  user-select: none;
  color: #8b8b8b;
  font-size: 12px;
  width: 16px;
  display: inline-block;
  text-align: center;
  flex-shrink: 0;
}

.expand-icon:hover {
  color: #404040;
}

.name-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.name-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.id-hint {
  font-size: 11px;
  color: #aaa;
  font-family: var(--font-family-mono);
  word-break: break-all;
}

.status-tag {
  display: inline-block;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
}

.tag-completed {
  background: transparent;
  color: #16a34a;
}

.tag-running {
  background: transparent;
  color: #2563eb;
}

.tag-pending {
  background: #f5f5f5;
  color: #8b8b8b;
}

.tag-failed {
  background: transparent;
  color: #dc2626;
  cursor: help;
  padding: 4px 14px;
  margin: -4px -6px;
}

.error-tooltip div {
  line-height: 1.6;
  max-width: 400px;
  word-break: break-word;
}

.tag-cancelled {
  background: #f5f5f5;
  color: #aaa;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar-bg {
  flex: 1;
  height: 6px;
  background: #e5e5e5;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}

.bar-running {
  background: #3b82f6;
}

.bar-completed {
  background: #22c55e;
}

.bar-failed {
  background: #ef4444;
}

.progress-text {
  font-size: 12px;
  color: #8b8b8b;
  white-space: nowrap;
}

.eta-tag {
  display: inline-block;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  background: #fff7ed;
  color: #c2410c;
  white-space: nowrap;
}

.action-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  height: 30px;
  padding: 0;
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
  color: #8b8b8b;
  font-size: 13px;
}

.empty-center {
  text-align: center;
}
</style>
