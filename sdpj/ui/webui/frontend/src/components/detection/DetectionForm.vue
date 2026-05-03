<template>
  <el-card class="detection-form">
    <template #header>
      <span>新建检测任务</span>
    </template>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
      <el-form-item label="模型ID" prop="model_id">
        <el-input v-model="form.model_id" placeholder="请输入模型ID" />
      </el-form-item>
      <el-form-item label="检测类型" prop="detection_type">
        <el-select v-model="form.detection_type" placeholder="请选择检测类型" style="width: 100%">
          <el-option label="静态检测" value="static" />
          <el-option label="动态检测" value="dynamic" />
          <el-option label="综合检测" value="comprehensive" />
        </el-select>
      </el-form-item>
      <el-form-item label="数据集" prop="dataset_ids">
        <el-select
          v-model="form.dataset_ids"
          multiple
          placeholder="请选择数据集"
          style="width: 100%"
          :loading="datasetsLoading"
        >
          <el-option
            v-for="ds in datasets"
            :key="ds.id"
            :label="ds.name"
            :value="ds.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="最大迭代次数" prop="max_iterations">
        <el-input-number
          v-model="form.max_iterations"
          :min="1"
          :max="1000"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          启动检测
        </el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { startDetection, getDatasets } from '../../api/detection'

const emit = defineEmits(['started'])

const formRef = ref()
const submitting = ref(false)
const datasetsLoading = ref(false)
const datasets = ref([])

const form = ref({
  model_id: '',
  detection_type: 'static',
  dataset_ids: [],
  max_iterations: 10
})

const rules = {
  model_id: [{ required: true, message: '请输入模型ID', trigger: 'blur' }],
  detection_type: [{ required: true, message: '请选择检测类型', trigger: 'change' }],
  dataset_ids: [{ required: true, type: 'array', min: 1, message: '请选择至少一个数据集', trigger: 'change' }]
}

const fetchDatasets = async () => {
  datasetsLoading.value = true
  try {
    const res = await getDatasets()
    datasets.value = Array.isArray(res) ? res : (res.datasets || [])
  } catch {
    datasets.value = []
  } finally {
    datasetsLoading.value = false
  }
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true
  try {
    const res = await startDetection(form.value)
    if (res.success) {
      ElMessage.success('检测任务已启动')
      emit('started', res)
      handleReset()
    }
  } catch {
    ElMessage.error('启动检测失败')
  } finally {
    submitting.value = false
  }
}

const handleReset = () => {
  formRef.value?.resetFields()
}

onMounted(fetchDatasets)
</script>
