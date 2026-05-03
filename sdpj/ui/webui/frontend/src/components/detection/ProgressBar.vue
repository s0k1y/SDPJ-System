<template>
  <div class="progress-bar">
    <div class="progress-header">
      <span class="task-id">{{ taskId }}</span>
      <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
    </div>
    <el-progress
      :percentage="percentage"
      :status="progressStatus"
      :stroke-width="12"
    />
    <div class="progress-footer" v-if="detail">
      <span>{{ detail }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  taskId: { type: String, default: '' },
  status: { type: String, default: 'pending' },
  percentage: { type: Number, default: 0 },
  detail: { type: String, default: '' }
})

const statusType = computed(() => {
  const map = {
    pending: 'info',
    running: '',
    completed: 'success',
    failed: 'danger'
  }
  return map[props.status] || 'info'
})

const statusText = computed(() => {
  const map = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return map[props.status] || props.status
})

const progressStatus = computed(() => {
  if (props.status === 'completed') return 'success'
  if (props.status === 'failed') return 'exception'
  return ''
})
</script>

<style scoped>
.progress-bar {
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.progress-bar:last-child {
  border-bottom: none;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-id {
  font-size: 13px;
  color: #606266;
  font-family: monospace;
}

.progress-footer {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}
</style>
