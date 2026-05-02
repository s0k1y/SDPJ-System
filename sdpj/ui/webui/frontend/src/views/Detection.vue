<template>
  <div class="detection">
    <h2>安全检测</h2>
    
    <el-card>
      <el-steps :active="currentStep" finish-status="success">
        <el-step title="选择模型" />
        <el-step title="选择数据集" />
        <el-step title="配置参数" />
        <el-step title="启动检测" />
      </el-steps>
      
      <div class="step-content">
        <div v-if="currentStep === 0">
          <h3>选择检测模型</h3>
          <el-select v-model="form.model_id" placeholder="请选择模型" style="width: 100%">
            <el-option label="GPT-4" value="gpt-4" />
            <el-option label="Claude-3" value="claude-3" />
            <el-option label="通义千问" value="qwen" />
          </el-select>
        </div>
        
        <div v-if="currentStep === 1">
          <h3>选择检测数据集</h3>
          <el-select v-model="form.dataset_id" placeholder="请选择数据集" style="width: 100%">
            <el-option label="JADE DB v1" :value="1" />
            <el-option label="JADE DB v2" :value="2" />
            <el-option label="自定义数据集" :value="3" />
          </el-select>
        </div>
        
        <div v-if="currentStep === 2">
          <h3>配置检测参数</h3>
          <el-form :model="form" label-width="120px">
            <el-form-item label="算法类型">
              <el-radio-group v-model="form.algorithm_type">
                <el-radio value="static">静态检测</el-radio>
                <el-radio value="dynamic">动态检测</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </div>
        
        <div v-if="currentStep === 3">
          <h3>确认并启动</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="模型">{{ form.model_id }}</el-descriptions-item>
            <el-descriptions-item label="数据集">{{ form.dataset_id }}</el-descriptions-item>
            <el-descriptions-item label="算法">{{ form.algorithm_type }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      
      <div class="step-actions">
        <el-button v-if="currentStep > 0" @click="currentStep--">上一步</el-button>
        <el-button v-if="currentStep < 3" type="primary" @click="currentStep++">下一步</el-button>
        <el-button v-if="currentStep === 3" type="success" @click="handleStart" :loading="loading">
          启动检测
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const currentStep = ref(0)
const loading = ref(false)

const form = ref({
  model_id: '',
  dataset_id: null,
  algorithm_type: 'static'
})

const handleStart = async () => {
  loading.value = true
  try {
    const res = await api.post('/detection/start', form.value)
    if (res.success) {
      ElMessage.success('检测任务已启动')
      currentStep.value = 0
      form.value = { model_id: '', dataset_id: null, algorithm_type: 'static' }
    }
  } catch (error) {
    ElMessage.error('启动失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.detection h2 {
  margin-bottom: 20px;
}

.step-content {
  margin: 40px 0;
  min-height: 200px;
}

.step-content h3 {
  margin-bottom: 20px;
}

.step-actions {
  text-align: center;
}
</style>
