<template>
  <el-card class="task-list">
    <template #header>
      <div class="card-header">
        <span>任务队列</span>
        <el-button size="small" @click="refresh" :loading="loading">
          刷新
        </el-button>
      </div>
    </template>

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
  </el-card>
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
    if (res.success) {
      tasks.value = res.queue || []
    }
  } catch {
    // 静默处理
  } finally {
    loading.value = false
  }
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
