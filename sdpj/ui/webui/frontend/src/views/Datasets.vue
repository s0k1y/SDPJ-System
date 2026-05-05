<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">检测数据集</h1>
      <p class="page-info">管理用于安全检测的提示词数据集</p>

      <div class="action-bar">
        <el-button class="btn-create" @click="openCreate" :icon="null">新建数据集</el-button>
        <el-button class="btn-import" @click="importVisible = true" :icon="null">导入数据集</el-button>
      </div>

      <div class="table-wrapper" v-loading="loading">
        <table>
          <thead>
            <tr>
              <th style="width: 20%">数据集ID</th>
              <th style="width: 30%">名称</th>
              <th style="width: 20%">样本数</th>
              <th style="width: 15%">创建时间</th>
              <th style="width: 15%">操作</th>
            </tr>
          </thead>
          <tbody v-if="datasets.length > 0">
            <tr v-for="ds in datasets" :key="ds.dataset_id || ds.id">
              <td><span class="cell-mono">{{ ds.dataset_id || ds.id }}</span></td>
              <td>{{ ds.name || '-' }}</td>
              <td>{{ ds.sample_count ?? '-' }}</td>
              <td>{{ ds.created_at || '-' }}</td>
              <td>
                <div class="action-btns">
                  <el-button class="action-btn" size="small" @click="viewDetail(ds)">查看</el-button>
                  <el-button class="action-btn action-btn-danger" size="small" @click="deleteDataset(ds)">删除</el-button>
                </div>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="99" class="empty-row">暂无数据集</td>
            </tr>
          </tbody>
        </table>
      </div>

      <el-dialog v-model="dialogVisible" title="新建数据集" width="500px">
        <el-form :model="formData" label-width="100px">
          <el-form-item label="数据集名称">
            <el-input v-model="formData.name" placeholder="请输入数据集名称" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false" :icon="null">取消</el-button>
          <el-button type="primary" @click="saveDataset" :loading="saving">创建</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="importVisible" title="导入数据集" width="500px">
        <el-upload
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          accept=".json,.csv"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">拖拽文件到此处或<em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">支持 JSON / CSV 格式</div>
          </template>
        </el-upload>
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
import { UploadFilled } from '@element-plus/icons-vue'
import api from '../api'

const datasets = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const importVisible = ref(false)
const saving = ref(false)
const importing = ref(false)
const file = ref(null)

const formData = ref({ name: '', description: '' })

const fetchDatasets = async () => {
  loading.value = true
  try {
    const res = await api.get('/datasets')
    datasets.value = res?.datasets || res?.data || []
  } catch { datasets.value = [] }
  finally { loading.value = false }
}

const openCreate = () => {
  formData.value = { name: '', description: '' }
  dialogVisible.value = true
}

const saveDataset = async () => {
  saving.value = true
  try {
    await api.post('/datasets', formData.value)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    fetchDatasets()
  } catch { ElMessage.error('创建失败') }
  finally { saving.value = false }
}

const viewDetail = (ds) => {
  ElMessage.info(`查看数据集: ${ds.name || ds.dataset_id || ds.id}`)
}

const deleteDataset = async (ds) => {
  await ElMessageBox.confirm('确认删除该数据集？', '提示', { type: 'warning' })
  try {
    await api.delete(`/datasets/${ds.dataset_id || ds.id}`)
    ElMessage.success('已删除')
    fetchDatasets()
  } catch { ElMessage.error('删除失败') }
}

const handleFileChange = (uploadFile) => {
  file.value = uploadFile.raw
}

const doImport = async () => {
  if (!file.value) return ElMessage.warning('请选择文件')
  importing.value = true
  try {
    const formPayload = new FormData()
    formPayload.append('file', file.value)
    await api.post('/datasets/import', formPayload, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('导入成功')
    importVisible.value = false
    fetchDatasets()
  } catch { ElMessage.error('导入失败') }
  finally { importing.value = false }
}

onMounted(fetchDatasets)
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

.table-wrapper {
  background: #fafafa;
  border-radius: 10px;
  padding: 2px 14px 4px;
  margin-bottom: 24px;
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

.action-btns {
  display: flex;
  align-items: center;
  gap: 8px;
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
}

.action-btn-danger:hover {
  color: #dc2626;
  background: rgba(239, 68, 68, 0.08);
}

.empty-row {
  padding: 24px 8px;
  text-align: center;
  color: #8b8b8b;
  font-size: 13px;
}
</style>
