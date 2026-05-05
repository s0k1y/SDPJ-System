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

      <div class="table-wrapper" v-loading="loading">
        <table>
          <thead>
            <tr>
              <th style="width: 15%">配置ID</th>
              <th style="width: 15%">资源ID</th>
              <th style="width: 15%">操作</th>
            </tr>
          </thead>
          <tbody v-if="configs.length > 0">
            <tr v-for="cfg in configs" :key="cfg.config_id">
              <td><span class="cell-mono">{{ cfg.config_id }}</span></td>
              <td><span class="cell-mono">{{ cfg.resource_id || '-' }}</span></td>
              <td>
                <el-button class="action-btn" size="small" @click="deleteConfig(cfg.config_id)">删除</el-button>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="99" class="empty-row">暂无配置</td>
            </tr>
          </tbody>
        </table>
      </div>

      <el-dialog v-model="dialogVisible" title="新建配置" width="500px">
        <el-form>
          <el-form-item label="配置内容 (JSON)">
            <el-input v-model="configJson" type="textarea" :rows="10" placeholder='{"key": "value"}' />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false" :icon="null">取消</el-button>
          <el-button type="primary" @click="saveConfig" :loading="saving">保存</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="importVisible" title="导入配置" width="500px">
        <el-form>
          <el-form-item label="配置内容 (JSON)">
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
import { encryptPassword } from '../utils/crypto'

const configs = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const importVisible = ref(false)
const configJson = ref('')
const importJson = ref('')
const saving = ref(false)
const importing = ref(false)

const encryptConfig = async (configContent) => {
  const jsonStr = JSON.stringify(configContent)
  return await encryptPassword(jsonStr)
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await detectionConfig('list', {})
    configs.value = res.success ? (res.configs || []) : []
  } catch { configs.value = [] }
  finally { loading.value = false }
}

const openCreate = () => {
  configJson.value = ''
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
    const encryptedContent = await encryptConfig(content)
    const res = await detectionConfig('create', {
      config_content: encryptedContent,
      is_encrypted: true
    })
    if (res.success) {
      ElMessage.success('创建成功')
      dialogVisible.value = false
      await loadList()
    } else {
      ElMessage.error(res.error || '操作失败')
    }
  } catch { ElMessage.error('操作失败') }
  finally { saving.value = false }
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
  color: #8b8b8b;
  font-weight: 600;
  font-size: 14px;
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid #e5e5e5;
}

td {
  color: #404040;
  font-size: 14px;
  padding: 10px 8px;
  vertical-align: middle;
}

.cell-mono {
  font-family: var(--font-family-mono);
  letter-spacing: 0.3px;
}

.action-btn {
  height: 30px;
  padding: 0 14px;
  font-size: 12px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #404040;
}

.action-btn:hover {
  background: #e5e5e5;
  color: #dc2626;
}

.empty-row {
  padding: 24px 8px;
  text-align: center;
  color: #8b8b8b;
  font-size: 13px;
}
</style>
