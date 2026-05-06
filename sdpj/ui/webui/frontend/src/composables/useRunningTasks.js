import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getProgress } from '../api/detection'

const runningCount = ref(0)
const pendingCount = ref(0)
let timer = null
let refCount = 0

function startPolling() {
  if (timer) return
  fetchProgress()
  timer = setInterval(fetchProgress, 5000)
}

function stopPolling() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

async function fetchProgress() {
  try {
    const res = await getProgress()
    if (res.success) {
      const queue = res.data?.queue || []
      runningCount.value = queue.filter(t => t.status === 'running').length
      pendingCount.value = queue.filter(t => t.status === 'pending').length
    }
  } catch {
    // 静默处理
  }
}

export function useRunningTasks() {
  const activeCount = computed(() => runningCount.value + pendingCount.value)
  const hasRunning = computed(() => runningCount.value > 0)
  const hasActive = computed(() => activeCount.value > 0)

  onMounted(() => {
    refCount++
    startPolling()
  })

  onUnmounted(() => {
    refCount--
    if (refCount <= 0) {
      refCount = 0
      stopPolling()
    }
  })

  return { runningCount, pendingCount, activeCount, hasRunning, hasActive, fetchProgress }
}
