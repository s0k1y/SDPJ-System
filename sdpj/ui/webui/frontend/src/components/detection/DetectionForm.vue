<template>
  <div class="detection-form">
    <div class="section-header">
      <h2 class="section-title">新建检测任务</h2>
    </div>

    <div class="steps-container">
      <el-steps :active="currentStep" align-center finish-status="success">
        <el-step title="上传被测大模型API调用配置文件" />
        <el-step title="选择待测数据集与参数" />
        <el-step title="确认并启动" />
      </el-steps>

      <div class="step-content">
        <el-form :model="form" :rules="rules" ref="formRef" label-width="130px" class="form-content">

          <div v-show="currentStep === 0">
            <el-form-item label="模型适配器" prop="model_id">
              <template v-if="!modelsLoading && modelAdapters.length === 0">
                <div class="empty-adapter-hint">
                  <span>暂无可用的模型适配器，请先</span>
                  <router-link to="/private-config" class="link">上传适配器</router-link>
                </div>
              </template>
              <template v-else>
                <el-select
                  v-model="form.model_id"
                  placeholder="请选择模型适配器"
                  style="width: 100%"
                  :loading="modelsLoading"
                >
                  <el-option
                    v-for="model in modelAdapters"
                    :key="model.config_id"
                    :label="getModelLabel(model)"
                    :value="model.config_id"
                  />
                </el-select>
              </template>
              <template #label>
                <span>模型适配器</span>
                <el-tooltip
                  content="选择已上传的大模型适配器配置，系统将使用该适配器对目标模型进行安全检测"
                  placement="top"
                >
                  <span class="tooltip-icon">?</span>
                </el-tooltip>
              </template>
            </el-form-item>

            <el-form-item label="检测类型" prop="detection_type">
              <el-select v-model="form.detection_type" placeholder="请选择检测类型" style="width: 100%">
                <el-option label="静态检测" value="static" />
                <el-option label="动态检测" value="dynamic" />
              </el-select>
              <template #label>
                <span>检测类型</span>
                <el-tooltip
                  content="静态检测：遍历检测样本库生成静态检测报告（Algorithm 1）；动态检测：在静态检测基础上进行迭代变异攻击（Algorithm 2，包含静态步骤）"
                  placement="top"
                >
                  <span class="tooltip-icon">?</span>
                </el-tooltip>
              </template>
            </el-form-item>
          </div>

          <div v-show="currentStep === 1">
            <el-form-item label="数据集" prop="dataset_ids">
              <el-tree-select
                v-model="form.dataset_ids"
                :data="datasetTree"
                multiple
                show-checkbox
                placeholder="请选择数据集"
                style="width: 100%"
                :loading="datasetsLoading"
                node-key="id"
                :props="{ label: 'label', children: 'children' }"
                @change="handleDatasetSelectionChange"
              />
              <template #label>
                <span>检测数据集</span>
                <el-tooltip
                  content="选择用于安全检测的提示词数据集，支持多选。数据集从左侧菜单的「检测数据集」页面上传"
                  placement="top"
                >
                  <span class="tooltip-icon">?</span>
                </el-tooltip>
              </template>
            </el-form-item>

            <el-form-item label="刷新PoC池">
              <el-switch v-model="form.force_refresh" />
              <template #label>
                <span>刷新PoC池</span>
                <el-tooltip
                  content="关闭时使用已缓存的PoC池（默认3个越狱数据集）；开启后可选择越狱数据集重新构建PoC池"
                  placement="top"
                >
                  <span class="tooltip-icon">?</span>
                </el-tooltip>
              </template>
            </el-form-item>

            <el-form-item v-if="form.force_refresh" label="越狱数据集">
              <el-tree-select
                v-model="form.jailbreak_dataset_ids"
                :data="jailbreakDatasetTree"
                multiple
                show-checkbox
                placeholder="请选择越狱数据集"
                style="width: 100%"
                :loading="datasetsLoading"
                node-key="id"
                :props="{ label: 'label', children: 'children' }"
                @change="handleJailbreakSelectionChange"
              />
              <template #label>
                <span>用于PoC池构建的越狱数据集</span>
                <el-tooltip
                  content="选择用于构建PoC池的越狱数据集"
                  placement="top"
                >
                  <span class="tooltip-icon">?</span>
                </el-tooltip>
              </template>
            </el-form-item>

            <el-form-item v-if="form.detection_type === 'dynamic'" label="最大迭代次数" prop="max_iterations">
              <el-input-number
                v-model="form.max_iterations"
                :min="1"
                :max="1000"
                style="width: 100%"
              />
              <template #label>
                <span>最大迭代次数</span>
                <el-tooltip
                  content="动态检测的最大交互轮数，数值越大检测越深入但耗时更长，建议 5-20"
                  placement="top"
                >
                  <span class="tooltip-icon">?</span>
                </el-tooltip>
              </template>
            </el-form-item>
          </div>

          <div v-show="currentStep === 2">
            <div class="summary-box">
              <div class="summary-row">
                <span class="summary-label">模型适配器</span>
                <span class="summary-value">{{ modelLabel }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">检测类型</span>
                <span class="summary-value">{{ detectionTypeLabel }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">检测数据集</span>
                <span class="summary-value">{{ datasetSummary }}</span>
              </div>
              <div v-if="form.force_refresh" class="summary-row">
                <span class="summary-label">用于PoC池构建的越狱数据集</span>
                <span class="summary-value">{{ jailbreakSummary }}</span>
              </div>
              <div v-if="form.detection_type === 'dynamic'" class="summary-row">
                <span class="summary-label">最大迭代次数</span>
                <span class="summary-value">{{ form.max_iterations }}</span>
              </div>
            </div>
          </div>

        </el-form>
      </div>

      <div class="step-actions">
        <el-button
          v-if="currentStep > 0"
          class="btn-prev"
          @click="prevStep"
        >上一步</el-button>

        <el-button
          v-if="currentStep < 2"
          class="btn-next"
          @click="nextStep"
          :disabled="modelsLoading && modelAdapters.length === 0"
        >下一步</el-button>

        <el-button
          v-if="currentStep === 2"
          class="btn-submit"
          @click="handleSubmit"
          :loading="submitting"
        >启动检测</el-button>

        <el-button class="btn-reset" @click="handleReset">重置</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { startDetection, getDatasets, detectionConfig } from '../../api/detection'
import { useDetectionStore } from '../../store'

const detectionStore = useDetectionStore()
const router = useRouter()

const formRef = ref()
const currentStep = ref(0)
const submitting = ref(false)
const datasetsLoading = ref(false)
const modelsLoading = ref(false)
const datasets = ref([])
const datasetTree = ref([])
const modelAdapters = ref([])

const jailbreakDatasets = ref([])
const jailbreakDatasetTree = ref([])

const form = ref({
  model_id: '',
  detection_type: 'static',
  dataset_ids: [],
  jailbreak_dataset_ids: [],
  max_iterations: 10,
  force_refresh: false
})

const rules = {
  model_id: [{ required: true, message: '请选择模型适配器', trigger: 'change' }],
  detection_type: [{ required: true, message: '请选择检测类型', trigger: 'change' }],
  dataset_ids: [{ required: true, type: 'array', min: 1, message: '请选择至少一个数据集', trigger: 'change' }]
}

const modelLabel = computed(() => {
  const selected = modelAdapters.value.find(m => m.config_id === form.value.model_id)
  return selected ? getModelLabel(selected) : (form.value.model_id || '-')
})

const detectionTypeLabel = computed(() => {
  const map = { static: '静态检测', dynamic: '动态检测' }
  return map[form.value.detection_type] || form.value.detection_type
})

const datasetSummary = computed(() => {
  if (!form.value.dataset_ids.length) return '-'
  return `${form.value.dataset_ids.length} 个数据集`
})

const jailbreakSummary = computed(() => {
  if (!form.value.force_refresh) return '使用缓存'
  const ids = form.value.jailbreak_dataset_ids
  if (!ids.length) return '未选择'
  return `重新构建 (${ids.length} 个越狱数据集)`
})

const leafJailbreakDatasetIds = computed(() => {
  const leafIds = new Set()
  jailbreakDatasets.value.forEach(ds => {
    leafIds.add(ds.dataset_id)
  })
  return leafIds
})

const leafDatasetIds = computed(() => {
  const leafIds = new Set()
  datasets.value.forEach(ds => {
    leafIds.add(ds.dataset_id)
  })
  return leafIds
})

const handleDatasetSelectionChange = (selectedIds) => {
  form.value.dataset_ids = selectedIds.filter(id => leafDatasetIds.value.has(id))
}

const handleJailbreakSelectionChange = (selectedIds) => {
  form.value.jailbreak_dataset_ids = selectedIds.filter(id => leafJailbreakDatasetIds.value.has(id))
}

const getModelLabel = (model) => {
  const content = model.content || {}
  const modelId = content.model_id || content.model || model.config_id
  const format = content.request_format
  if (format === 'openai') {
    return `${modelId} (OpenAI)`
  } else if (format === 'anthropic') {
    return `${modelId} (Anthropic)`
  } else {
    return modelId
  }
}

const validateStep = async (step) => {
  if (step === 0) {
    await formRef.value.validateField('model_id')
    await formRef.value.validateField('detection_type')
  } else if (step === 1) {
    await formRef.value.validateField('dataset_ids')
  }
}

const nextStep = async () => {
  try {
    await validateStep(currentStep.value)
    currentStep.value++
  } catch { /* 校验不通过 */ }
}

const prevStep = () => {
  currentStep.value--
}

const buildDatasetTree = (datasets) => {
  const tree = []
  const pathMap = new Map()

  datasets.forEach(ds => {
    const normalizedName = ds.name.replace(/\\/g, '/')
    const parts = normalizedName.split('/')
    let currentLevel = tree
    let currentPath = ''

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part
      const isLeaf = index === parts.length - 1

      if (isLeaf) {
        currentLevel.push({ id: ds.dataset_id, label: part, isLeaf: true })
      } else {
        let node = pathMap.get(currentPath)
        if (!node) {
          node = { id: currentPath, label: part, children: [] }
          currentLevel.push(node)
          pathMap.set(currentPath, node)
        }
        currentLevel = node.children
      }
    })
  })

  const hasUserDatasets = tree.some(node => node.label === 'user_datasets')
  if (!hasUserDatasets) {
    tree.push({ id: 'user_datasets', label: 'user_datasets', children: [] })
  }

  return tree
}

const fetchDatasets = async () => {
  datasetsLoading.value = true
  try {
    const res = await getDatasets()
    const allDatasets = res.data || []

    const jailbreak = []
    const nonJailbreak = []
    for (const ds of allDatasets) {
      if (ds.risk_type === 'jailbreak') {
        jailbreak.push(ds)
      } else {
        nonJailbreak.push(ds)
      }
    }

    datasets.value = nonJailbreak
    jailbreakDatasets.value = jailbreak
    datasetTree.value = buildDatasetTree(nonJailbreak)
    jailbreakDatasetTree.value = buildDatasetTree(jailbreak)
    const defaultStems = ['jailbreak_llm', 'augmented_jailbreak', 'jailbreakv_28k']
    form.value.jailbreak_dataset_ids = jailbreak
      .filter(ds => {
        const stem = ds.name.replace(/\\/g, '/').split('/').pop().toLowerCase()
        return defaultStems.includes(stem)
      })
      .map(ds => ds.dataset_id)
  } catch {
    datasets.value = []
    jailbreakDatasets.value = []
    datasetTree.value = []
  } finally {
    datasetsLoading.value = false
  }
}

const fetchModelAdapters = async () => {
  modelsLoading.value = true
  try {
    const res = await detectionConfig('list', {})
    modelAdapters.value = res.success ? (res.data?.configs || []) : []
  } catch {
    modelAdapters.value = []
  } finally {
    modelsLoading.value = false
  }
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true
  try {
    const selectedModel = modelAdapters.value.find(m => m.config_id === form.value.model_id)
    const realModelId = selectedModel?.content?.model_id || selectedModel?.content?.model || form.value.model_id
    const payload = {
      model_id: realModelId,
      config_id: form.value.model_id,
      detection_type: form.value.detection_type,
      dataset_ids: form.value.dataset_ids,
      jailbreak_dataset_ids: form.value.force_refresh ? form.value.jailbreak_dataset_ids : [],
      max_iterations: form.value.max_iterations,
      force_refresh: form.value.force_refresh
    }
    const res = await startDetection(payload)
    if (res.success) {
      ElMessage.success('检测任务已启动')
      detectionStore.addTask(res.data)
      detectionStore.setCurrentTask(res.data)
      handleReset()
      router.push('/dashboard')
    }
  } catch {
    ElMessage.error('启动检测失败')
  } finally {
    submitting.value = false
  }
}

const handleReset = () => {
  formRef.value?.resetFields()
  currentStep.value = 0
}

onMounted(() => {
  fetchDatasets()
  fetchModelAdapters()
})
</script>

<style scoped>
.detection-form {
  margin-bottom: 42px;
}

.section-header {
  margin-bottom: 21px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #404040;
  margin: 0;
}

.steps-container {
  max-width: 520px;
}

:deep(.el-steps) {
  margin-bottom: 0;
}

:deep(.el-step__title) {
  font-size: 14px;
  font-weight: 500;
  color: #404040;
  white-space: normal;
  line-height: 1.4;
}

.step-content {
  margin-top: 20px;
  min-height: 100px;
}

.form-content {
  max-width: 520px;
}

.tooltip-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-left: 6px;
  border-radius: 50%;
  background: #e5e5e5;
  color: #8b8b8b;
  font-size: 11px;
  font-weight: 600;
  cursor: help;
  line-height: 1;
}

.tooltip-icon:hover {
  background: #d0d0d0;
  color: #404040;
}

.empty-adapter-hint {
  font-size: 14px;
  color: #8b8b8b;
  padding: 8px 0;
}

.empty-adapter-hint .link {
  color: rgb(59, 130, 246);
  text-decoration: none;
}

.empty-adapter-hint .link:hover {
  text-decoration: underline;
}

.summary-box {
  background: #fafafa;
  border-radius: 10px;
  padding: 16px 20px;
}

.summary-row {
  display: flex;
  padding: 10px 0;
  border-bottom: 1px solid #e5e5e5;
}

.summary-row:last-child {
  border-bottom: none;
}

.summary-label {
  font-size: 14px;
  color: #8b8b8b;
  width: 110px;
  flex-shrink: 0;
}

.summary-value {
  font-size: 14px;
  color: #404040;
  font-weight: 500;
}

.step-actions {
  margin-top: 0px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-next {
  height: 34px;
  padding: 0 14px;
  font-size: 14px;
  border-radius: 10px;
  background: #000;
  color: #fff;
  border: none;
}

.btn-next:hover {
  background: #333;
}

.btn-next.is-disabled {
  background: #d0d0d0;
  color: #8b8b8b;
}

.btn-prev {
  height: 34px;
  padding: 0 14px;
  font-size: 14px;
  border-radius: 10px;
  border: 1px solid #d0d0d0;
  color: #404040;
  background: #fff;
}

.btn-prev:hover {
  background: #f5f5f5;
}

.btn-submit {
  height: 34px;
  padding: 0 14px;
  font-size: 14px;
  border-radius: 10px;
  background: #000;
  color: #fff;
  border: none;
}

.btn-submit:hover {
  background: #333;
}

.btn-reset {
  height: 34px;
  padding: 0 14px;
  font-size: 14px;
  border-radius: 10px;
  border: 1px solid #d0d0d0;
  color: #404040;
  background: #fff;
}

.btn-reset:hover {
  background: #f5f5f5;
}
</style>
