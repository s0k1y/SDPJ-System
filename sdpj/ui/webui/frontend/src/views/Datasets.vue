<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">检测数据集</h1>
      <p class="page-info">管理用于安全检测的提示词数据集</p>

      <div class="action-bar">
        <el-button class="btn-import" @click="importVisible = true" :icon="null">导入数据集</el-button>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th style="width: 35%">数据集名称</th>
              <th style="width: 20%; min-width: 80px;">样本数</th>
              <th style="width: 20%">创建时间</th>
              <th style="width: 25%">操作</th>
            </tr>
          </thead>
          <template v-if="flattenedTree.length > 0">
            <template v-for="item in flattenedTree" :key="item.id">
              <tr :class="{ 'folder-row': !item.isLeaf, 'dataset-row': item.isLeaf }">
                <td>
                  <div class="name-cell" :style="{ paddingLeft: (item.level * 20) + 'px' }">
                    <span v-if="!item.isLeaf" class="folder-icon" @click="toggleExpand(item)">
                      {{ item.expanded ? '▼' : '▶' }}
                    </span>
                    <span v-else class="file-icon">📄</span>
                    <span class="name-text">{{ item.label }}</span>
                  </div>
                </td>
                <td>
                  <span v-if="item.isLeaf" class="sample-count">{{ item.sample_count ?? '-' }}</span>
                  <span v-else class="folder-summary">{{ item.childCount }} 项</span>
                </td>
                <td>{{ item.isLeaf ? (formatDateTime(item.created_at)) : '-' }}</td>
                <td>
                  <div class="action-btns" v-if="item.isLeaf">
                    <el-button class="action-btn" size="small" @click="exportDataset(item)">导出</el-button>
                    <el-button v-if="item.name && item.name.startsWith('user_datasets/')" class="action-btn action-btn-danger" size="small" @click="deleteDataset(item)">删除</el-button>
                  </div>
                </td>
              </tr>
            </template>
          </template>
          <tbody v-else-if="!loading && flattenedTree.length === 0">
            <tr>
              <td colspan="99" class="empty-row"><div class="empty-center" style="margin-right: 37%;">暂无数据集</div></td>
            </tr>
          </tbody>
        </table>
      </div>

      <el-dialog v-model="importVisible" title="导入数据集" width="500px">
        <el-upload
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          accept=".json,.jsonl,.csv"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">拖拽文件到此处或<em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">支持 JSON / JSONL / CSV 格式</div>
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
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '../api'

const datasets = ref([])
const datasetTree = ref([])
const loading = ref(true)
const importVisible = ref(false)
const importing = ref(false)
const file = ref(null)

const formData = ref({ name: '', description: '' })

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  const d = new Date(datetime)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// 构建树形结构（与 DetectionForm 相同的逻辑）
const buildDatasetTree = (datasets) => {
  const tree = []
  const pathMap = new Map()

  datasets.forEach(ds => {
    // 统一处理 / 和 \ 两种路径分隔符
    const normalizedName = ds.name.replace(/\\/g, '/')
    const parts = normalizedName.split('/')
    let currentLevel = tree
    let currentPath = ''

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part
      const isLeaf = index === parts.length - 1

      if (isLeaf) {
        currentLevel.push({
          id: ds.dataset_id,
          label: part,
          isLeaf: true,
          sample_count: ds.sample_count,
          created_at: ds.created_at,
          dataset_id: ds.dataset_id,
          name: ds.name
        })
      } else {
        let node = pathMap.get(currentPath)
        if (!node) {
          node = {
            id: currentPath,
            label: part,
            children: [],
            isLeaf: false,
            expanded: true // 默认展开
          }
          currentLevel.push(node)
          pathMap.set(currentPath, node)
        }
        currentLevel = node.children
      }
    })
  })

  // 确保 user_datasets 始终存在
  const hasUserDatasets = tree.some(node => node.label === 'user_datasets')
  if (!hasUserDatasets) {
    tree.push({
      id: 'user_datasets',
      label: 'user_datasets',
      children: [],
      isLeaf: false,
      expanded: true
    })
  }

  return tree
}

// 计算子项数量
const countChildren = (node) => {
  if (node.isLeaf) return 0
  let count = 0
  if (node.children) {
    node.children.forEach(child => {
      if (child.isLeaf) {
        count++
      } else {
        count += countChildren(child)
      }
    })
  }
  return count
}

// 扁平化树形结构用于渲染
const flattenTree = (tree, level = 0) => {
  const result = []
  tree.forEach(node => {
    const item = { ...node, level }
    if (!node.isLeaf) {
      item.childCount = countChildren(node)
    }
    result.push(item)
    if (!node.isLeaf && node.expanded && node.children) {
      result.push(...flattenTree(node.children, level + 1))
    }
  })
  return result
}

const flattenedTree = computed(() => flattenTree(datasetTree.value))

// 切换展开/折叠
const toggleExpand = (item) => {
  const toggleNode = (tree) => {
    for (const node of tree) {
      if (node.id === item.id) {
        node.expanded = !node.expanded
        // 强制触发响应式更新
        datasetTree.value = [...datasetTree.value]
        return true
      }
      if (node.children && toggleNode(node.children)) {
        return true
      }
    }
    return false
  }
  toggleNode(datasetTree.value)
}

const fetchDatasets = async () => {
  loading.value = true
  try {
    const res = await api.get('/detection/datasets')
    datasets.value = res.data || []
    datasetTree.value = buildDatasetTree(datasets.value)
  } catch {
    datasets.value = []
    datasetTree.value = []
  }
  finally { loading.value = false }
}

const exportDataset = async (ds) => {
  try {
    // 调用后端导出接口，获取文件流
    const response = await api.get(`/detection/datasets/${ds.dataset_id}/export`, {
      responseType: 'blob'
    })

    // 创建下载链接
    const blob = new Blob([response], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // 使用数据集名称的最后一段作为文件名
    const fileName = (ds.name || `dataset_${ds.dataset_id}`).split('/').pop().split('\\').pop() + '.jsonl'
    link.download = fileName

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (err) {
    ElMessage.error('导出失败')
  }
}

const deleteDataset = async (ds) => {
  await ElMessageBox.confirm('确认删除该数据集？', '提示', { type: 'warning' })
  try {
    const res = await api.delete(`/detection/datasets/${ds.dataset_id || ds.id}`)
    if (res.success === false) {
      ElMessage.error(res.message || '删除失败')
    } else {
      ElMessage.success('已删除')
      fetchDatasets()
    }
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
    const res = await api.post('/detection/datasets/import', formPayload, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.success === false) {
      ElMessage.error(res.message || '导入失败')
    } else {
      ElMessage.success('导入成功')
      importVisible.value = false
      fetchDatasets()
    }
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

.btn-import {
  height: 34px;
  padding: 0 14px;
  font-size: 14px;
  border-radius: 10px;
  background: #000;
  color: #fff;
  border: none;
}

.btn-import:hover {
  background: #333;
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

.action-btns {
  display: flex;
  align-items: center;
  gap: 8px;
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

.empty-row {
  padding: 24px 8px;
  color: #8b8b8b;
  font-size: 13px;
}

.empty-center {
  text-align: center;
}

/* 树形结构样式 */
.folder-row {
  background: #f5f5f5;
  font-weight: 500;
}

.dataset-row:hover {
  background: #f9f9f9;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.folder-icon {
  cursor: pointer;
  user-select: none;
  color: #8b8b8b;
  font-size: 12px;
  width: 16px;
  display: inline-block;
  text-align: center;
}

.folder-icon:hover {
  color: #404040;
}

.file-icon {
  font-size: 14px;
  width: 16px;
  display: inline-block;
  text-align: center;
}

.name-text {
  flex: 1;
}

.folder-summary {
  color: #8b8b8b;
  font-size: 13px;
}

.sample-count {
  white-space: nowrap;
}
</style>
