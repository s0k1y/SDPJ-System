<template>
  <div class="detection-form">
    <div class="steps-container">
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

            <el-form-item label="检测算法" prop="detection_type">
              <el-select v-model="form.detection_type" placeholder="请选择检测算法" style="width: 100%">
                <el-option label="静态检测" value="static" />
                <el-option label="动态检测" value="dynamic" />
              </el-select>
              <template #label>
                <span>检测算法</span>
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
            <el-form-item label="攻击路径" prop="attack_paths">
              <el-tree-select
                v-model="form.attack_paths"
                :data="attackPathTree"
                multiple
                show-checkbox
                placeholder="请选择攻击路径"
                style="width: 100%"
                node-key="id"
                :props="{ label: 'label', children: 'children' }"
              />
              <template #label>
                <span>攻击路径</span>
                <el-tooltip
                  content="选择检测攻击路径：直接注入为原始PoC直接发送；间接注入通过编码变换PoC后再发送，可多选"
                  placement="top"
                >
                  <span class="tooltip-icon">?</span>
                </el-tooltip>
              </template>
            </el-form-item>
            <el-alert
              v-if="multimodalWarning"
              :title="multimodalWarning"
              type="warning"
              :closable="false"
              show-icon
              style="margin-top: -8px; margin-bottom: 16px"
            />
          </div>

          <div v-show="currentStep === 3">
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
              <div class="summary-row">
                <span class="summary-label">攻击路径</span>
                <span class="summary-value">{{ attackPathSummary }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">子任务数</span>
                <span class="summary-value">{{ subtaskCount }}
                  <span v-if="subtaskCount > 20" class="subtask-warn">（子任务数较多，检测耗时可能较长）</span>
                </span>
              </div>
              <div v-if="form.force_refresh" class="summary-row">
                <span class="summary-label">用于PoC池构建的越狱数据集</span>
                <span class="summary-value">{{ jailbreakSummary }}</span>
              </div>
              <div v-if="form.detection_type === 'dynamic'" class="summary-row">
                <span class="summary-label">最大迭代次数</span>
                <span class="summary-value">{{ form.max_iterations }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">每秒最大请求数</span>
                <span class="summary-value">{{ form.max_rps != null ? form.max_rps : maxRpsPlaceholder }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">最大并发数</span>
                <span class="summary-value">{{ form.max_concurrency != null ? form.max_concurrency : maxConcurrencyPlaceholder }}</span>
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
          v-if="currentStep < 3"
          class="btn-next"
          @click="nextStep"
          :disabled="(modelsLoading && modelAdapters.length === 0) || (currentStep === 2 && hasUnsupportedMultimodal)"
        >下一步</el-button>

        <el-button
          v-if="currentStep === 3"
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { startDetection, getDatasets, detectionConfig, getEncodingTypes } from '../../api/detection'
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

const encodingTypes = ref([])
const multimodalSupportedTypes = ref([])
const multimodalWarning = ref('')

const attackPathTree = computed(() => buildAttackPathTree(encodingTypes.value, !isOpenAiAdapter.value))

const form = ref({
  model_id: '',
  detection_type: 'static',
  dataset_ids: [],
  jailbreak_dataset_ids: [],
  max_iterations: 3,
  force_refresh: false,
  attack_paths: []
})

watch(() => form.value.model_id, () => {
  checkMultimodalCapability()
})

watch(() => form.value.attack_paths, () => {
  updateMultimodalWarning()
}, { deep: true })

const rules = {
  model_id: [{ required: true, message: '请选择模型适配器', trigger: 'change' }],
  detection_type: [{ required: true, message: '请选择检测算法', trigger: 'change' }],
  dataset_ids: [{ required: true, type: 'array', min: 1, message: '请选择至少一个数据集', trigger: 'change' }],
  attack_paths: [{ required: true, type: 'array', min: 1, message: '请至少选择一种攻击路径', trigger: 'change' }]
}

const _MULTIMODAL_IDS = new Set(MULTIMODAL_CHILDREN.map(c => c.id))
const _CONTENT_TYPE_MAP = Object.fromEntries(MULTIMODAL_CHILDREN.map(c => [c.id, c.contentType]))

const isOpenAiAdapter = computed(() => {
  const selected = modelAdapters.value.find(m => m.config_id === form.value.model_id)
  return selected?.content?.request_format === 'openai'
})

const checkMultimodalCapability = async () => {
  if (!form.value.model_id || !isOpenAiAdapter.value) {
    multimodalSupportedTypes.value = []
    return
  }
  try {
    const res = await detectionConfig('multimodal_check', { config_id: form.value.model_id })
    multimodalSupportedTypes.value = res.success ? (res.data?.result?.supported_types || []) : []
  } catch {
    multimodalSupportedTypes.value = []
  }
}

const updateMultimodalWarning = () => {
  const selected = form.value.attack_paths.filter(id => _MULTIMODAL_IDS.has(id))
  if (selected.length === 0) {
    multimodalWarning.value = ''
    return
  }
  if (!isOpenAiAdapter.value) {
    multimodalWarning.value = '多模态注入检测仅支持 OpenAI 兼容格式的被测模型'
    return
  }
  const unsupported = selected.filter(id => {
    const ct = _CONTENT_TYPE_MAP[id]
    return ct && !multimodalSupportedTypes.value.includes(ct)
  })
  if (unsupported.length > 0) {
    const types = [...new Set(unsupported.map(id => _CONTENT_TYPE_MAP[id]))]
    const typeLabel = types.map(t => t === 'image_url' ? '图像(image_url)' : '音频(input_audio)').join('、')
    multimodalWarning.value = `被测模型不支持该模态(${typeLabel})。请先在私有配置页面进行多模态能力测试，或取消选择该攻击路径`
  } else {
    multimodalWarning.value = ''
  }
}

const effectiveAttackPaths = computed(() => {
  return form.value.attack_paths.filter(id =>
    id === 'direct' || _MULTIMODAL_IDS.has(id) || _ENCODING_LEAF_IDS.value.has(id)
  )
})

const attackPathSummary = computed(() => {
  const paths = effectiveAttackPaths.value
  if (!paths.length) return '-'
  const parts = []
  if (paths.includes('direct')) parts.push('直接注入')
  const multimodal = paths.filter(p => p.startsWith('multi-modal:')).map(p => p.split(':')[1])
  if (multimodal.length) parts.push(`多模态(${multimodal.join(', ')})`)
  const encoding = paths.filter(p => p !== 'direct' && !p.startsWith('multi-modal:'))
  if (encoding.length) parts.push(`多编码(${encoding.join(', ')})`)
  return parts.join(' + ')
})

const subtaskCount = computed(() => {
  const dsCount = form.value.dataset_ids.length || 0
  const pathCount = effectiveAttackPaths.value.length || 0
  return dsCount * pathCount
})

const hasUnsupportedMultimodal = computed(() => {
  const selected = form.value.attack_paths.filter(id => _MULTIMODAL_IDS.has(id))
  if (selected.length === 0) return false
  if (!isOpenAiAdapter.value) return true
  return selected.some(id => {
    const ct = _CONTENT_TYPE_MAP[id]
    return ct && !multimodalSupportedTypes.value.includes(ct)
  })
})

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

const maxRpsPlaceholder = computed(() => {
  const selected = modelAdapters.value.find(m => m.config_id === form.value.model_id)
  const val = selected?.content?.max_rps
  return val != null ? val : 0.5
})

const maxConcurrencyPlaceholder = computed(() => {
  const selected = modelAdapters.value.find(m => m.config_id === form.value.model_id)
  const val = selected?.content?.max_concurrency
  return val != null ? val : 3
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
  } else if (step === 2) {
    await formRef.value.validateField('attack_paths')
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
    for (const ds of allDatasets) {
      if (ds.risk_type === 'jailbreak') {
        jailbreak.push(ds)
      }
    }

    datasets.value = allDatasets
    jailbreakDatasets.value = jailbreak
    datasetTree.value = buildDatasetTree(allDatasets)
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

const _ENCODING_LEAF_IDS = computed(() => new Set(encodingTypes.value.map(t => t.name)))

const MULTIMODAL_CHILDREN = [
  { id: 'multi-modal:txt', label: 'TXT 文本', contentType: 'file' },
  { id: 'multi-modal:mhtml', label: 'MHTML 文本', contentType: 'file' },
  { id: 'multi-modal:jpg', label: 'JPG 图像', contentType: 'image_url' },
  { id: 'multi-modal:png', label: 'PNG 图像', contentType: 'image_url' },
  { id: 'multi-modal:mp3', label: 'MP3 音频', contentType: 'input_audio' },
  { id: 'multi-modal:wav', label: 'WAV 音频', contentType: 'input_audio' },
]

const buildAttackPathTree = (types, disableMultimodal = false) => {
  return [
    { id: 'direct', label: '直接注入' },
    {
      id: 'indirect_injection',
      label: '间接注入',
      children: [
        {
          id: 'multimodal',
          label: '多模态注入',
          disabled: disableMultimodal,
          children: MULTIMODAL_CHILDREN.map(c => ({
            ...c,
            disabled: disableMultimodal,
          })),
        },
        {
          id: 'multi_encoding',
          label: '多编码注入',
          children: types.map(t => ({
            id: t.name,
            label: `${t.label}${t.chinese_compatible ? '' : ' (仅对英文PoC有效)'}`,
          }))
        }
      ]
    }
  ]
}

const fetchEncodingTypes = async () => {
  try {
    const res = await getEncodingTypes()
    if (res.success) {
      encodingTypes.value = res.data || []
    }
  } catch {
    encodingTypes.value = []
  }
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true
  try {
    const selectedModel = modelAdapters.value.find(m => m.config_id === form.value.model_id)
    const realModelId = selectedModel?.content?.model_id || selectedModel?.content?.model || form.value.model_id
    const paths = effectiveAttackPaths.value
    const hasDirect = paths.includes('direct')
    const modalities = paths
      .filter(p => p.startsWith('multi-modal:'))
      .map(p => p.split(':')[1])
    const encodingTypes = paths.filter(p => p !== 'direct' && !p.startsWith('multi-modal:'))
    const payload = {
      model_id: realModelId,
      config_id: form.value.model_id,
      detection_type: form.value.detection_type,
      dataset_ids: form.value.dataset_ids,
      jailbreak_dataset_ids: form.value.force_refresh ? form.value.jailbreak_dataset_ids : [],
      max_iterations: form.value.max_iterations,
      force_refresh: form.value.force_refresh,
      has_direct: hasDirect,
      encoding_types: encodingTypes.length > 0 ? encodingTypes : null,
      modalities: modalities.length > 0 ? modalities : null,
    }
    const res = await startDetection(payload)
    if (res.success) {
      ElMessage.success('检测任务已启动')
      detectionStore.addTask(res.data)
      detectionStore.setCurrentTask(res.data)
      handleReset()
      router.push('/dashboard')
    } else {
      ElMessage.error(res.message || '启动检测失败')
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '启动检测失败')
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
  fetchEncodingTypes()
})

defineExpose({ currentStep })
</script>

<style scoped>
.detection-form {
  margin-bottom: 42px;
}

.steps-container {
  max-width: 520px;
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

.subtask-warn {
  font-size: 12px;
  color: #f59e0b;
  font-weight: 400;
}
</style>
