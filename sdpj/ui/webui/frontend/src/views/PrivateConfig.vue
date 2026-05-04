<template>
  <PageLayout title="私有配置" description="管理用户私有的大模型适配器和检测配置">
    <div class="action-bar">
      <el-button type="primary" @click="openCreate">新建配置</el-button>
      <el-button @click="loadList">刷新</el-button>
      <el-button @click="importVisible = true">导入配置</el-button>
    </div>

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
  </PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { detectionConfig } from '../api/detection'
import { encryptPassword, decryptData } from '../utils/crypto'
import PageLayout from '../components/common/PageLayout.vue'

const configs = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const importVisible = ref(false)
const editingId = ref(null)
const configJson = ref('')
const importJson = ref('')
const saving = ref(false)
const importing = ref(false)

// 加密配置内容
const encryptConfig = async (configContent) => {
  const jsonStr = JSON.stringify(configContent)
  // 使用 RSA 加密
  return await encryptPassword(jsonStr)
}

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
    if (res.success && res.config_content) {
      // 服务端已解密，直接解析
      let content = res.config_content
      if (typeof content === 'string') {
        try {
          content = JSON.parse(content)
        } catch {
          // 如果解析失败，直接使用字符串
        }
      }
      // 格式化显示
      configJson.value = typeof content === 'object'
        ? JSON.stringify(content, null, 2)
        : content
    } else {
      ElMessage.warning('无法读取配置内容')
      configJson.value = ''
    }
  } catch (error) {
    console.error('读取配置失败:', error)
    ElMessage.error('读取配置失败')
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

    // 加密配置内容
    const encryptedContent = await encryptConfig(content)

    const params = editingId.value
      ? { config_id: editingId.value, config_content: encryptedContent, is_encrypted: true }
      : { config_content: encryptedContent, is_encrypted: true }

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
  try {
    const res = await detectionConfig('export', { config_id: configId, target_format: 'json' })
    if (res.success) {
      let content = res.file_content

      // 服务端已解密，直接使用
      if (typeof content === 'object') {
        content = JSON.stringify(content, null, 2)
      }

      // 创建下载
      const blob = new Blob([content], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `config_${configId}.json`
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
    } else {
      ElMessage.error(res.error || '导出失败')
    }
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
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
    // 加密配置内容
    const encryptedContent = await encryptConfig(content)

    const res = await detectionConfig('import', {
      file_content: encryptedContent,
      is_encrypted: true
    })
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

<style scoped>
.action-bar {
  display: flex;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-6);
}
</style>
