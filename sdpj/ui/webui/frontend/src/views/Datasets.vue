<template>
  <PageLayout title="检测数据集" description="查看系统内置和用户私有的检测数据集">
    <el-card>
      <!-- 操作栏 -->
      <div class="action-bar">
        <el-button type="primary" @click="openUploadDialog">上传数据集</el-button>
        <el-button @click="loadDatasets">刷新</el-button>
        <div class="search-wrapper">
          <el-input
            v-model="searchText"
            placeholder="搜索数据集名称或风险类型"
            clearable
            style="width: 300px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <!-- 数据表格 -->
      <el-table
        :data="filteredDatasets"
        v-loading="loading"
        style="width: 100%"
        :empty-text="searchText ? '未找到匹配的数据集' : '暂无数据集'"
      >
        <el-table-column prop="dataset_id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="200" />
        <el-table-column prop="risk_type" label="风险类型" width="150">
          <template #default="{ row }">
            <el-tag :type="getRiskTypeTag(row.risk_type)" size="small">
              {{ row.risk_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sample_count" label="样本数" width="100" align="right" />
        <el-table-column prop="is_builtin" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_builtin ? 'info' : 'success'" size="small">
              {{ row.is_builtin ? '系统内置' : '用户私有' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDataset(row)">查看</el-button>
            <template v-if="!row.is_builtin">
              <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteDataset(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <div v-if="!loading && datasets.length === 0" class="empty-state">
        <el-empty description="暂无数据集" />
      </div>
    </el-card>

    <!-- 上传数据集对话框 -->
    <el-dialog v-model="uploadVisible" title="上传数据集" width="600px">
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="数据集名称" required>
          <el-input v-model="uploadForm.name" placeholder="请输入数据集名称" />
        </el-form-item>
        <el-form-item label="风险类型" required>
          <el-select v-model="uploadForm.risk_type" placeholder="请选择风险类型">
            <el-option label="越狱" value="越狱" />
            <el-option label="隐私" value="隐私" />
            <el-option label="毒性" value="毒性" />
            <el-option label="偏见" value="偏见" />
            <el-option label="幻觉" value="幻觉" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据集文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".csv,.json,.jsonl"
            :on-change="handleFileChange"
          >
            <el-button>选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 CSV、JSON、JSONL 格式</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>

    <!-- 编辑数据集对话框 -->
    <el-dialog v-model="editVisible" title="编辑数据集" width="600px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="数据集名称" required>
          <el-input v-model="editForm.name" placeholder="请输入数据集名称" />
        </el-form-item>
        <el-form-item label="风险类型" required>
          <el-select v-model="editForm.risk_type" placeholder="请选择风险类型">
            <el-option label="越狱" value="越狱" />
            <el-option label="隐私" value="隐私" />
            <el-option label="毒性" value="毒性" />
            <el-option label="偏见" value="偏见" />
            <el-option label="幻觉" value="幻觉" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit" :loading="editing">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看数据集详情对话框 -->
    <el-dialog v-model="viewVisible" title="数据集详情" width="70%">
      <el-descriptions :column="2" border v-if="currentDataset">
        <el-descriptions-item label="数据集ID">{{ currentDataset.dataset_id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ currentDataset.name }}</el-descriptions-item>
        <el-descriptions-item label="风险类型">
          <el-tag :type="getRiskTypeTag(currentDataset.risk_type)" size="small">
            {{ currentDataset.risk_type }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="样本数">{{ currentDataset.sample_count }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="currentDataset.is_builtin ? 'info' : 'success'" size="small">
            {{ currentDataset.is_builtin ? '系统内置' : '用户私有' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentDataset.created_at || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </PageLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDatasets, detectionResource } from '../api/detection'
import PageLayout from '../components/common/PageLayout.vue'

const loading = ref(false)
const datasets = ref([])
const searchText = ref('')

const uploadVisible = ref(false)
const editVisible = ref(false)
const viewVisible = ref(false)
const uploading = ref(false)
const editing = ref(false)

const uploadForm = ref({
  name: '',
  risk_type: '',
  file: null
})

const editForm = ref({
  dataset_id: '',
  name: '',
  risk_type: ''
})

const currentDataset = ref(null)

// 过滤数据集
const filteredDatasets = computed(() => {
  if (!searchText.value) return datasets.value
  const keyword = searchText.value.toLowerCase()
  return datasets.value.filter(item =>
    item.name?.toLowerCase().includes(keyword) ||
    item.risk_type?.toLowerCase().includes(keyword)
  )
})

// 风险类型标签颜色
const getRiskTypeTag = (riskType) => {
  const typeMap = {
    '越狱': 'danger',
    '隐私': 'warning',
    '毒性': 'danger',
    '偏见': 'warning',
    '幻觉': 'info'
  }
  return typeMap[riskType] || 'info'
}

const loadDatasets = async () => {
  loading.value = true
  try {
    const res = await getDatasets()
    datasets.value = Array.isArray(res) ? res : (res.datasets || [])
  } catch (error) {
    console.error('加载数据集失败:', error)
    ElMessage.error('加载数据集失败')
  } finally {
    loading.value = false
  }
}

const openUploadDialog = () => {
  uploadForm.value = {
    name: '',
    risk_type: '',
    file: null
  }
  uploadVisible.value = true
}

const handleFileChange = (file) => {
  uploadForm.value.file = file.raw
}

const handleUpload = async () => {
  if (!uploadForm.value.name) {
    ElMessage.warning('请输入数据集名称')
    return
  }
  if (!uploadForm.value.risk_type) {
    ElMessage.warning('请选择风险类型')
    return
  }
  if (!uploadForm.value.file) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('name', uploadForm.value.name)
    formData.append('risk_type', uploadForm.value.risk_type)

    const res = await detectionResource('upload_dataset', {
      name: uploadForm.value.name,
      risk_type: uploadForm.value.risk_type,
      file_content: await uploadForm.value.file.text()
    })

    if (res.success) {
      ElMessage.success('上传成功')
      uploadVisible.value = false
      await loadDatasets()
    } else {
      ElMessage.error(res.error || '上传失败')
    }
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const openEditDialog = (row) => {
  editForm.value = {
    dataset_id: row.dataset_id,
    name: row.name,
    risk_type: row.risk_type
  }
  editVisible.value = true
}

const handleEdit = async () => {
  if (!editForm.value.name) {
    ElMessage.warning('请输入数据集名称')
    return
  }
  if (!editForm.value.risk_type) {
    ElMessage.warning('请选择风险类型')
    return
  }

  editing.value = true
  try {
    const res = await detectionResource('update_dataset', {
      dataset_id: editForm.value.dataset_id,
      name: editForm.value.name,
      risk_type: editForm.value.risk_type
    })

    if (res.success) {
      ElMessage.success('更新成功')
      editVisible.value = false
      await loadDatasets()
    } else {
      ElMessage.error(res.error || '更新失败')
    }
  } catch (error) {
    console.error('更新失败:', error)
    ElMessage.error('更新失败')
  } finally {
    editing.value = false
  }
}

const deleteDataset = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除数据集"${row.name}"吗？`, '确认删除', {
      type: 'warning'
    })

    const res = await detectionResource('delete_dataset', {
      dataset_id: row.dataset_id
    })

    if (res.success) {
      ElMessage.success('删除成功')
      await loadDatasets()
    } else {
      ElMessage.error(res.error || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const viewDataset = (row) => {
  currentDataset.value = row
  viewVisible.value = true
}

onMounted(() => {
  loadDatasets()
})
</script>

<style scoped>
.action-bar {
  display: flex;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
  align-items: center;
}

.search-wrapper {
  margin-left: auto;
}

.empty-state {
  padding: var(--spacing-8) 0;
}
</style>
