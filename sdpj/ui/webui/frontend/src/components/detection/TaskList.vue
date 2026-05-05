<template>
  <div class="task-list">
    <div class="section-header">
      <h2 class="section-title">任务队列</h2>
      <el-button class="btn-refresh" size="small" @click="refresh" :loading="loading">刷新</el-button>
    </div>

    <div v-if="loading && tasks.length === 0">
      <el-skeleton :rows="3" animated />
    </div>

    <el-empty v-else-if="tasks.length === 0" description="暂无任务" />

    <div v-else>
      <ProgressBar
        v-for="task in tasks"
        :key="task.task_id"
        :task-id="task.task_id"
        :status="task.status"
        :percentage="task.progress || 0"
        :detail="task.detail || ''"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getProgress } from '../../api/detection'
import ProgressBar from './ProgressBar.vue'

const tasks = ref([])
const loading = ref(false)
let timer = null

const refresh = async () => {
  loading.value = true
  try {
    const res = await getProgress()
    if (res.success) tasks.value = res.queue || []
  } catch { /* 静默处理 */ }
  finally { loading.value = false }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 5000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
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

.btn-refresh {
  height: 30px;
  padding: 0 14px;
  font-size: 12px;
  border-radius: 10px;
  border: 1px solid #d0d0d0;
  color: #404040;
  background: #fff;
}

.btn-refresh:hover {
  background: #f5f5f5;
}
</style>
