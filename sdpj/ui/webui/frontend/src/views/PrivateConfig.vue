<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">私有配置</h1>
      <p class="page-info">管理用户私有的大模型适配器和检测配置</p>

      <div class="action-bar">
        <el-button class="btn-create" @click="openCreate" :icon="null">新建配置</el-button>
        <el-button class="btn-import" @click="importVisible = true" :icon="null">导入配置</el-button>
        <el-button class="btn-refresh" @click="loadList" :icon="null">刷新</el-button>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th style="width: 15%">配置ID</th>
              <th style="width: 20%">模型ID</th>
              <th style="width: 15%">格式</th>
              <th style="width: 30%">API地址</th>
              <th style="width: 20%">操作</th>
            </tr>
          </thead>
          <tbody v-if="configs.length > 0">
            <tr v-for="cfg in configs" :key="cfg.config_id">
              <td><span class="cell-mono">{{ cfg.config_id }}</span></td>
              <td><span class="cell-mono">{{ getModelId(cfg) }}</span></td>
              <td>{{ getFormat(cfg) }}</td>
              <td class="url-cell">{{ getApiUrl(cfg) }}</td>
              <td>
                <div class="action-btns">
                  <el-button class="action-btn" size="small" @click="viewConfig(cfg)">查看</el-button>
                  <el-button class="action-btn" size="small" @click="editConfig(cfg)">编辑</el-button>
                  <el-button class="action-btn" size="small" @click="verifyConfig(cfg)" :loading="verifyingId === cfg.config_id">可用性测试</el-button>
                  <el-button class="action-btn" size="small" @click="testMultimodal(cfg)" :loading="multimodalTestingId === cfg.config_id" :disabled="!isOpenAiFormat(cfg)">多模态测试</el-button>
                  <el-button class="action-btn action-btn-danger" size="small" @click="deleteConfig(cfg.config_id)">删除</el-button>
                </div>
              </td>
            </tr>
          </tbody>
          <tbody v-else-if="!loading && configs.length === 0">
            <tr>
              <td colspan="99" class="empty-row"><div class="empty-center" style="margin-right: 36%;">暂无配置</div></td>
            </tr>
          </tbody>
        </table>
      </div>

      <el-dialog v-model="dialogVisible" :title="editingConfigId ? '编辑配置' : '新建配置'" width="700px">
        <el-form>
          <el-form-item label="选择模板">
            <el-select v-model="selectedTemplate" placeholder="请选择适配器模板" @change="applyTemplate" style="width: 100%">
              <el-option label="OpenAI 格式" value="openai" />
              <el-option label="Anthropic 格式" value="anthropic" />
              <el-option label="系统抽象规范" value="custom" />
            </el-select>
          </el-form-item>

          <el-alert
            :title="templateGuide.title"
            :description="templateGuide.description"
            type="info"
            :closable="false"
            style="margin-bottom: 16px"
          />

          <el-form-item label="配置内容 (JSON)" label-position="top">
            <el-input v-model="configJson" type="textarea" :rows="14" placeholder='{"key": "value"}' />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false" :icon="null">取消</el-button>
          <el-button type="primary" @click="saveConfig" :loading="saving">保存</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="importVisible" title="导入配置" width="500px">
        <el-form>
          <el-form-item label="选择模板">
            <el-select v-model="selectedTemplate" placeholder="请选择适配器模板" @change="applyTemplate" style="width: 100%">
              <el-option label="OpenAI 格式" value="openai" />
              <el-option label="Anthropic 格式" value="anthropic" />
              <el-option label="系统抽象规范" value="custom" />
            </el-select>
          </el-form-item>

          <el-alert
            :title="templateGuide.title"
            :description="templateGuide.description"
            type="info"
            :closable="false"
            style="margin-bottom: 16px"
          />

          <el-form-item label="配置文件">
            <el-upload
              :auto-upload="false"
              :on-change="handleFileChange"
              :show-file-list="false"
              accept=".json,.jsonl"
            >
              <el-button :icon="null">选择文件 (JSON/JSONL)</el-button>
            </el-upload>
          </el-form-item>

          <el-form-item label="配置内容 (JSON)" label-position="top">
            <el-input v-model="importJson" type="textarea" :rows="10" placeholder='{"key": "value"}' />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="importVisible = false" :icon="null">取消</el-button>
          <el-button type="primary" @click="doImport" :loading="importing">导入</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { detectionConfig } from '../api/detection'

const configs = ref([])
const loading = ref(true)
const dialogVisible = ref(false)
const importVisible = ref(false)
const configJson = ref('')
const importJson = ref('')
const saving = ref(false)
const importing = ref(false)
const verifyingId = ref(null)
const multimodalTestingId = ref(null)
const selectedTemplate = ref('openai')
const editingConfigId = ref(null) // 正在编辑的配置ID

const templates = {
  openai: {
    model: "gpt-4",
    request_format: "openai",
    api_key: "your-openai-api-key",
    base_url: "https://api.openai.com/v1",
    timeout: 60,
    max_rps: 0.5,
    max_concurrency: 3
  },
  anthropic: {
    model: "claude-3-opus-20240229",
    request_format: "anthropic",
    api_key: "your-anthropic-api-key",
    base_url: "https://api.anthropic.com",
    timeout: 60,
    max_rps: 0.5,
    max_concurrency: 3
  },
  custom: {
    model_id: "custom/my-model",
    api_key: "your-api-key",
    api_endpoint: "https://your-api.com/v1/chat",
    timeout: 60,
    max_rps: 0.5,
    max_concurrency: 3
  }
}

const templateGuides = {
  openai: {
    title: 'OpenAI 格式适配器',
    description: '适用于所有兼容 OpenAI Chat Completions API 的大模型服务（OpenAI、DeepSeek、通义千问、Moonshot 等）。必需字段：model_id、request_format、api_key、base_url、model。可选字段：max_rps（每秒最大请求数，默认 0.5）、max_concurrency（最大并发数，默认 3）。免费 API 建议 max_rps=0.5、max_concurrency=3；付费 API 建议 max_rps=5.0、max_concurrency=10。'
  },
  anthropic: {
    title: 'Anthropic 格式适配器',
    description: '适用于 Anthropic Claude 系列及兼容 Anthropic API 的服务。必需字段：model_id、request_format、api_key、base_url、model。可选字段：max_rps（每秒最大请求数，默认 0.5）、max_concurrency（最大并发数，默认 3）。注意：DeepSeek 的 Anthropic 端点 base_url 需填写 https://api.deepseek.com/anthropic。'
  },
  custom: {
    title: '系统抽象规范',
    description: '使用系统内部统一的抽象接口。系统会自动将配置参数适配到统一的调用接口，无需指定 request_format。适用于任意符合系统抽象规范的大模型 API。必需字段：model_id、api_key、api_endpoint。可选字段：max_rps（每秒最大请求数，默认 0.5）、max_concurrency（最大并发数，默认 3）。'
  }
}

const templateGuide = ref(templateGuides.openai)

const loadList = async () => {
  loading.value = true
  try {
    const res = await detectionConfig('list', {})
    configs.value = res.success ? (res.data?.configs || []) : []
  } catch { configs.value = [] }
  finally { loading.value = false }
}

const openCreate = () => {
  editingConfigId.value = null
  selectedTemplate.value = 'openai'
  configJson.value = JSON.stringify(templates.openai, null, 2)
  templateGuide.value = templateGuides.openai
  dialogVisible.value = true
}

const applyTemplate = () => {
  const template = templates[selectedTemplate.value]
  configJson.value = JSON.stringify(template, null, 2)
  templateGuide.value = templateGuides[selectedTemplate.value]
}

const handleFileChange = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    const content = e.target.result
    // 支持 JSON 和 JSONL 格式
    if (file.name.endsWith('.jsonl')) {
      // JSONL 格式：每行一个 JSON 对象，取第一行
      const firstLine = content.split('\n')[0].trim()
      if (firstLine) {
        importJson.value = firstLine
      }
    } else {
      // JSON 格式
      importJson.value = content
    }
  }
  reader.readAsText(file.raw)
}

const saveConfig = async () => {
  let content
  try {
    content = JSON.parse(configJson.value)
  } catch {
    ElMessage.error('JSON 格式错误')
    return
  }
  saving.value = true
  try {
    const operation = editingConfigId.value ? 'update' : 'create'
    const params = {
      config_content: content
    }

    if (editingConfigId.value) {
      params.config_id = editingConfigId.value
    }

    const res = await detectionConfig(operation, params)
    if (res.success) {
      ElMessage.success(editingConfigId.value ? '更新成功' : '创建成功')
      dialogVisible.value = false
      editingConfigId.value = null
      await loadList()
    } else {
      ElMessage.error(res.message || '操作失败')
    }
  } catch { ElMessage.error('操作失败') }
  finally { saving.value = false }
}

const getModelId = (cfg) => {
  const content = cfg.content || {}
  return content.model_id || content.model || '-'
}

const getFormat = (cfg) => {
  const content = cfg.content || {}
  const format = content.request_format
  if (format === 'openai') return 'OpenAI'
  if (format === 'anthropic') return 'Anthropic'
  if (!format) return '系统抽象'
  return format
}

const getApiUrl = (cfg) => {
  const content = cfg.content || {}
  return content.base_url || content.api_url || content.api_endpoint || '-'
}

const viewConfig = (cfg) => {
  ElMessageBox.alert(
    `<pre style="max-height: 400px; overflow: auto; background: #f5f5f5; padding: 12px; border-radius: 4px;">${JSON.stringify(cfg.content, null, 2)}</pre>`,
    '配置详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭'
    }
  )
}

const editConfig = (cfg) => {
  editingConfigId.value = cfg.config_id
  configJson.value = JSON.stringify(cfg.content, null, 2)

  // 根据配置内容自动选择模板
  const content = cfg.content || {}
  if (content.request_format === 'openai') {
    selectedTemplate.value = 'openai'
    templateGuide.value = templateGuides.openai
  } else if (content.request_format === 'anthropic') {
    selectedTemplate.value = 'anthropic'
    templateGuide.value = templateGuides.anthropic
  } else {
    selectedTemplate.value = 'custom'
    templateGuide.value = templateGuides.custom
  }

  dialogVisible.value = true
}

const deleteConfig = async (configId) => {
  await ElMessageBox.confirm('确认删除该配置？', '提示', { type: 'warning' })
  const res = await detectionConfig('delete', { config_id: configId })
  if (res.success) {
    ElMessage.success('已删除')
    await loadList()
  } else {
    ElMessage.error(res.message || '删除失败')
  }
}

const verifyConfig = async (cfg) => {
  verifyingId.value = cfg.config_id
  try {
    const res = await detectionConfig('verify', { config_id: cfg.config_id })
    if (res.success && res.data?.result) {
      const r = res.data.result
      const lines = []
      lines.push(`<div style="font-size:14px;line-height:2;">`)
      lines.push(`<div><b>状态：</b><span style="color:#16a34a">✓ 连接成功</span></div>`)
      lines.push(`<div><b>模型：</b>${r.model || '-'}</div>`)
      lines.push(`<div><b>延迟：</b>${r.latency_ms}ms</div>`)
      if (r.response_preview) {
        lines.push(`<div><b>响应预览：</b>${r.response_preview}</div>`)
      }
      lines.push(`</div>`)
      ElMessageBox.alert(lines.join(''), '配置可用性验证', { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' })
    } else if (res.data?.result) {
      const r = res.data.result
      const statusMap = {
        auth_failed: '认证失败',
        unreachable: '端点不可达',
        format_mismatch: '格式不匹配',
        timeout: '验证超时',
        config_error: '配置错误',
        unknown_error: '未知错误',
      }
      const lines = []
      lines.push(`<div style="font-size:14px;line-height:2;">`)
      lines.push(`<div><b>状态：</b><span style="color:#dc2626">✗ ${statusMap[r.status] || r.status}</span></div>`)
      if (r.latency_ms) lines.push(`<div><b>延迟：</b>${r.latency_ms}ms</div>`)
      if (r.error) lines.push(`<div><b>错误详情：</b><code style="font-size:12px;word-break:break-all;">${r.error}</code></div>`)
      lines.push(`</div>`)
      ElMessageBox.alert(lines.join(''), '配置可用性验证', { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' })
    } else {
      const errMsg = res.message || res.data?.error || '未知错误'
      ElMessageBox.alert(`<div style="font-size:14px;"><b>状态：</b><span style="color:#dc2626">✗ 验证失败</span><br/><b>详情：</b>${errMsg}</div>`, '配置可用性验证', { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' })
    }
  } catch (e) {
    const isTimeout = e.code === 'ECONNABORTED' || e.message?.includes('timeout')
    const msg = isTimeout ? '验证超时(60s)，目标模型响应过慢或网络不通' : `请求失败: ${e.message || '网络错误'}`
    ElMessageBox.alert(`<div style="font-size:14px;"><b>状态：</b><span style="color:#dc2626">✗ ${isTimeout ? '超时' : '网络错误'}</span><br/><b>详情：</b>${msg}</div>`, '配置可用性验证', { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' })
  } finally {
    verifyingId.value = null
  }
}

const isOpenAiFormat = (cfg) => {
  const content = cfg.content || {}
  return content.request_format === 'openai'
}

const testMultimodal = async (cfg) => {
  multimodalTestingId.value = cfg.config_id
  try {
    const res = await detectionConfig('multimodal_test', { config_id: cfg.config_id })
    if (res.success && res.data?.result) {
      const r = res.data.result
      const supported = r.supported_types || []
      const typeMap = { image_url: '图像 (image_url)', input_audio: '音频 (input_audio)' }
      const lines = []
      lines.push(`<div style="font-size:14px;line-height:2;">`)
      if (supported.length > 0) {
        lines.push(`<div><b>状态：</b><span style="color:#16a34a">✓ 支持多模态</span></div>`)
        lines.push(`<div><b>支持的 content type：</b></div>`)
        for (const t of supported) {
          lines.push(`<div style="padding-left:16px;">${typeMap[t] || t} <span style="color:#16a34a">✓</span></div>`)
        }
      } else {
        const reason = r.reason || 'unknown'
        const reasonMap = { 'non-openai-format': '非 OpenAI 兼容格式', 'unknown': '未知原因' }
        lines.push(`<div><b>状态：</b><span style="color:#dc2626">✗ 不支持多模态</span></div>`)
        lines.push(`<div><b>原因：</b>${reasonMap[reason] || reason}</div>`)
      }
      lines.push(`</div>`)
      ElMessageBox.alert(lines.join(''), '多模态能力测试', { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' })
    } else {
      const errMsg = res.message || res.data?.error || '未知错误'
      ElMessageBox.alert(`<div style="font-size:14px;"><b>状态：</b><span style="color:#dc2626">✗ 测试失败</span><br/><b>详情：</b>${errMsg}</div>`, '多模态能力测试', { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' })
    }
  } catch (e) {
    const isTimeout = e.code === 'ECONNABORTED' || e.message?.includes('timeout')
    const msg = isTimeout ? '测试超时，目标模型响应过慢或网络不通' : `请求失败: ${e.message || '网络错误'}`
    ElMessageBox.alert(`<div style="font-size:14px;"><b>状态：</b><span style="color:#dc2626">✗ ${isTimeout ? '超时' : '网络错误'}</span><br/><b>详情：</b>${msg}</div>`, '多模态能力测试', { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' })
  } finally {
    multimodalTestingId.value = null
  }
}

const doImport = async () => {
  let content
  try {
    content = JSON.parse(importJson.value)
  } catch {
    ElMessage.error('JSON 格式错误')
    return
  }
  importing.value = true
  try {
    const res = await detectionConfig('import', {
      file_content: content
    })
    if (res.success) {
      ElMessage.success('导入成功')
      importVisible.value = false
      await loadList()
    } else {
      ElMessage.error(res.message || '导入失败')
    }
  } catch { ElMessage.error('导入失败') }
  finally { importing.value = false }
}

onMounted(loadList)
</script>

<style scoped>
.page-container {
  width: 100%;
}

.page-inner {
  max-width: 936px;
  margin: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #404040;
  line-height: 32px;
  margin: 0 0 32px;
}

.page-info {
  font-size: 14px;
  color: #404040;
  line-height: 25px;
  margin: 0 0 22px;
}

.action-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.btn-create {
  height: 34px;
  padding: 0 14px;
  font-size: 14px;
  border-radius: 10px;
  background: #000;
  color: #fff;
  border: none;
}

.btn-create:hover {
  background: #333;
}

.btn-import {
  height: 34px;
  padding: 0 14px;
  font-size: 14px;
  border-radius: 10px;
  border: 1px solid #d0d0d0;
  color: #404040;
  background: #fff;
}

.btn-import:hover {
  background: #f5f5f5;
}

.btn-refresh {
  height: 34px;
  padding: 0 14px;
  font-size: 14px;
  border-radius: 10px;
  border: 1px solid #d0d0d0;
  color: #404040;
  background: #fff;
}

.btn-refresh:hover {
  background: #f5f5f5;
}

.table-wrapper {
  background: #fafafa;
  border-radius: 10px;
  padding: 2px 14px 4px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th {
  color: #333333;
  font-weight: 600;
  font-size: 14px;
  text-align: left;
  padding: 10px 8px;
  border-top: 2px solid #333333;
  border-bottom: 1px solid #333333;
}

td {
  color: #404040;
  font-size: 14px;
  padding: 10px 8px;
  vertical-align: middle;
  border: none;
}

table tr:last-child td {
  border-bottom: 2px solid #333333;
}

.cell-mono {
  font-family: var(--font-family-mono);
  letter-spacing: 0.3px;
}

.action-btn {
  height: 30px;
  padding: 0;
  font-size: 12px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #404040;
}

.action-btn:hover {
  background: #e5e5e5;
}

.action-btn-danger:hover {
  color: #dc2626;
  background: rgba(239, 68, 68, 0.08);
}

.action-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

.url-cell {
  font-size: 13px;
  color: #666;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-row {
  padding: 24px 8px;
  color: #8b8b8b;
  font-size: 13px;
}

.empty-center {
  text-align: center;
}
</style>
