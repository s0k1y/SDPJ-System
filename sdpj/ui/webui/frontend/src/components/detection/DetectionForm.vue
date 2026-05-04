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
        <el-tree-select
          v-model="form.dataset_ids"
          :data="datasetTree"
          multiple
          show-checkbox
          check-strictly
          placeholder="请选择数据集"
          style="width: 100%"
          :loading="datasetsLoading"
          node-key="id"
          :props="{ label: 'label', children: 'children' }"
        />
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
const datasetTree = ref([])

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

// 将扁平的数据集列表转换为树形结构
const buildDatasetTree = (datasets) => {
  const tree = []
  const pathMap = new Map()

  datasets.forEach(ds => {
    const parts = ds.name.split('/')
    let currentLevel = tree
    let currentPath = ''

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part
      const isLeaf = index === parts.length - 1

      if (isLeaf) {
        // 叶子节点（实际的数据集）
        currentLevel.push({
          id: ds.dataset_id,
          label: part,
          isLeaf: true
        })
      } else {
        // 目录节点
        let node = pathMap.get(currentPath)
        if (!node) {
          node = {
            id: currentPath,
            label: part,
            children: [],
            disabled: true // 目录节点不可选
          }
          currentLevel.push(node)
          pathMap.set(currentPath, node)
        }
        currentLevel = node.children
      }
    })
  })

  // 确保 user_datasets 节点始终存在（即使为空）
  const hasUserDatasets = tree.some(node => node.label === 'user_datasets')
  if (!hasUserDatasets) {
    tree.push({
      id: 'user_datasets',
      label: 'user_datasets',
      children: [],
      disabled: true
    })
  }

  return tree
}

const fetchDatasets = async () => {
  datasetsLoading.value = true
  try {
    const res = await getDatasets()
    datasets.value = Array.isArray(res) ? res : (res.datasets || [])
    datasetTree.value = buildDatasetTree(datasets.value)
  } catch {
    datasets.value = []
    datasetTree.value = []
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
