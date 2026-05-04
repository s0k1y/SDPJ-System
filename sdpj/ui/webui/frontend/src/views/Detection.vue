<template>
  <PageLayout max-width="1400px">
    <template #header>
      <div class="header-content">
        <h1 class="page-title">安全检测</h1>
        <p class="page-description">配置并启动大模型安全风险检测任务</p>
      </div>
    </template>

    <div class="detection-grid">
      <!-- 检测表单 -->
      <div class="detection-form-section">
        <DetectionForm @started="onTaskStarted" />
      </div>

      <!-- 任务列表 -->
      <div class="task-list-section">
        <TaskList ref="taskListRef" />
      </div>
    </div>

    <!-- 批量运行控制 -->
    <div class="batch-control-card">
      <div class="batch-header">
        <div class="batch-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
          </svg>
          <span>批量运行</span>
        </div>
        <div class="batch-description">配置并发参数，批量执行队列中的检测任务</div>
      </div>
      <div class="batch-controls">
        <div class="control-group">
          <label class="control-label">最大并发数</label>
          <el-input-number
            v-model="maxConcurrency"
            :min="1"
            :max="10"
            size="large"
            class="concurrency-input"
          />
        </div>
        <el-button
          type="primary"
          size="large"
          @click="handleRunAll"
          :loading="runLoading"
          class="run-button"
        >
          <svg v-if="!runLoading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          {{ runLoading ? '运行中...' : '运行队列' }}
        </el-button>
      </div>
    </div>
  </PageLayout>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageLayout from '../components/common/PageLayout.vue'
import { runDetection } from '../api/detection'
import DetectionForm from '../components/detection/DetectionForm.vue'
import TaskList from '../components/detection/TaskList.vue'

const taskListRef = ref()
const maxConcurrency = ref(1)
const runLoading = ref(false)

const onTaskStarted = () => {
  taskListRef.value?.refresh()
}

const handleRunAll = async () => {
  runLoading.value = true
  try {
    const res = await runDetection(maxConcurrency.value)
    if (res.success) {
      ElMessage.success('检测队列已开始运行')
      taskListRef.value?.refresh()
    }
  } catch {
    ElMessage.error('运行失败')
  } finally {
    runLoading.value = false
  }
}
</script>

<style scoped>
.header-content {
  max-width: 800px;
}

.page-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  margin-bottom: var(--spacing-2);
  line-height: 1.2;
}

.page-description {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  margin: 0;
}

/* 检测网格 */
.detection-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-6);
}

.detection-form-section,
.task-list-section {
  min-width: 0;
}

/* 批量控制卡片 */
.batch-control-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.batch-header {
  margin-bottom: var(--spacing-5);
}

.batch-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--spacing-2);
}

.batch-title svg {
  width: 20px;
  height: 20px;
  color: var(--color-primary);
}

.batch-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.batch-controls {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-4);
}

.control-group {
  flex: 0 0 auto;
}

.control-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  margin-bottom: var(--spacing-2);
}

.concurrency-input {
  width: 160px;
}

.run-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-6);
  font-weight: var(--font-weight-semibold);
}

.run-button svg {
  width: 16px;
  height: 16px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .detection-grid {
    grid-template-columns: 1fr;
  }

  /* 移动端优先显示任务列表 */
  .task-list-section {
    order: -1;
  }
}

@media (max-width: 640px) {
  .page-title {
    font-size: var(--font-size-2xl);
  }

  .batch-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .concurrency-input {
    width: 100%;
  }

  .run-button {
    width: 100%;
    justify-content: center;
  }
}
</style>
