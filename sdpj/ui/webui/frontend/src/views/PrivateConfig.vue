<template>
  <div>
    <h2>私有检测配置</h2>
    <el-button type="primary" @click="openCreate" style="margin-bottom:16px">新建配置</el-button>
    <el-button @click="loadList" style="margin-bottom:16px">刷新</el-button>

    <el-table :data="configs" v-loading="loading">
      <el-table-column prop="config_id" label="配置ID" width="100" />
      <el-table-column prop="resource_id" label="资源ID" width="100" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" @click="exportConfig(row.config_id)">导出</el-button>
          <el-button size="small" type="danger" @click="deleteConfig(row.config_id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑配置' : '新建配置'" width="600px">
      <el-form>
        <el-form-item label="配置内容 (JSON)">
          <el-input v-model="configJson" type="textarea" :rows="10" placeholder='{"key": "value"}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importVisible" title="导入配置" width="600px">
      <el-form>
        <el-form-item label="配置内容 (JSON)">
          <el-input v-model="importJson" type="textarea" :rows="10" placeholder='{"key": "value"}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" @click="doImport" :loading="importing">导入</el-button>
      </template>
    </el-dialog>

    <el-button @click="importVisible = true" style="margin-top:16px">导入配置</el-button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { detectionConfig } from '../api/detection'

const configs = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const importVisible = ref(false)
const editingId = ref(null)
const configJson = ref('')
const importJson = ref('')
const saving = ref(false)
const importing = ref(false)

const loadList = async () => {
  loading.value = true
  try {
    const res = await detectionConfig('list', {})
    configs.value = res.success ? (res.configs || []) : []
  } catch {
    configs.value = []
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingId.value = null
  configJson.value = ''
  dialogVisible.value = true
}

const openEdit = async (row) => {
  editingId.value = row.config_id
  try {
    const res = await detectionConfig('read', { config_id: row.config_id })
    configJson.value = res.success ? JSON.stringify(res.config_content, null, 2) : ''
  } catch {
    configJson.value = ''
  }
  dialogVisible.value = true
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
    const op = editingId.value ? 'update' : 'create'
    const params = editingId.value
      ? { config_id: editingId.value, config_content: content }
      : { config_content: content }
    const res = await detectionConfig(op, params)
    if (res.success) {
      ElMessage.success(editingId.value ? '更新成功' : '创建成功')
      dialogVisible.value = false
      await loadList()
    } else {
      ElMessage.error(res.error || '操作失败')
    }
  } catch {
    ElMessage.error('操作失败')
  } finally {
    saving.value = false
  }
}

const deleteConfig = async (configId) => {
  await ElMessageBox.confirm('确认删除该配置？', '提示', { type: 'warning' })
  const res = await detectionConfig('delete', { config_id: configId })
  if (res.success) {
    ElMessage.success('已删除')
    await loadList()
  } else {
    ElMessage.error(res.error || '删除失败')
  }
}

const exportConfig = async (configId) => {
  const res = await detectionConfig('export', { config_id: configId, target_format: 'json' })
  if (res.success) {
    const blob = new Blob([res.file_content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `config_${configId}.json`
    a.click()
    URL.revokeObjectURL(url)
  } else {
    ElMessage.error(res.error || '导出失败')
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
    const res = await detectionConfig('import', { file_content: content })
    if (res.success) {
      ElMessage.success('导入成功')
      importVisible.value = false
      await loadList()
    } else {
      ElMessage.error(res.error || '导入失败')
    }
  } catch {
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

onMounted(loadList)
</script>
