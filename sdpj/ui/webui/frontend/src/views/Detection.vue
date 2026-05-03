<template>
  <div class="detection">
    <h2>安全检测</h2>

    <el-row :gutter="20">
      <el-col :span="14">
        <DetectionForm @started="onTaskStarted" />
      </el-col>
      <el-col :span="10">
        <TaskList ref="taskListRef" />
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>批量运行</span>
        </div>
      </template>
      <el-form inline>
        <el-form-item label="最大并发数">
          <el-input-number v-model="maxConcurrency" :min="1" :max="10" />
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="handleRunAll" :loading="runLoading">
            运行队列
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
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
.detection h2 {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
