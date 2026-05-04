<template>
  <PageLayout title="系统日志" description="查看和筛选系统操作日志">
    <el-card class="filter-card">
      <el-form :model="filters" label-width="100px" @submit.prevent="handleSearch">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="日志类别">
              <el-select v-model="filters.category" placeholder="全部" clearable>
                <el-option label="应用日志" value="app" />
                <el-option label="错误日志" value="error" />
                <el-option label="访问日志" value="access" />
                <el-option label="审计日志" value="audit" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="来源模块">
              <el-input v-model="filters.source_module" placeholder="如: SDPJDetector" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="用户ID">
              <el-input v-model="filters.user_id" placeholder="用户ID" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="timeRange"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24" style="text-align: right">
            <el-button @click="handleReset">重置</el-button>
            <el-button type="primary" @click="handleSearch" :loading="loading">查询</el-button>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table :data="logs" v-loading="loading" style="width: 100%">
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="category" label="类别" width="100">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)" size="small">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)" size="small">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_module" label="来源模块" width="150" />
        <el-table-column prop="user_id" label="用户ID" width="120" />
        <el-table-column prop="message" label="日志内容" min-width="300" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无日志数据" />
        </template>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="60%">
      <el-descriptions :column="1" border v-if="selectedLog">
        <el-descriptions-item label="时间">{{ selectedLog.timestamp }}</el-descriptions-item>
        <el-descriptions-item label="类别">
          <el-tag :type="getCategoryType(selectedLog.category)" size="small">
            {{ getCategoryLabel(selectedLog.category) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="级别">
          <el-tag :type="getLevelType(selectedLog.level)" size="small">
            {{ selectedLog.level }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="来源模块">{{ selectedLog.source_module }}</el-descriptions-item>
        <el-descriptions-item label="用户ID">{{ selectedLog.user_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="日志内容">
          <pre class="log-content">{{ selectedLog.message }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="额外信息" v-if="selectedLog.extra">
          <pre class="log-content">{{ JSON.stringify(selectedLog.extra, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </PageLayout>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import PageLayout from '../components/common/PageLayout.vue'
import { getLogList } from '../api/log'

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const timeRange = ref([])

const filters = reactive({
  category: '',
  source_module: '',
  user_id: ''
})

const detailVisible = ref(false)
const selectedLog = ref(null)

const getCategoryType = (category) => {
  const map = {
    app: 'info',
    error: 'danger',
    access: 'success',
    audit: 'warning'
  }
  return map[category] || 'info'
}

const getCategoryLabel = (category) => {
  const map = {
    app: '应用',
    error: '错误',
    access: '访问',
    audit: '审计'
  }
  return map[category] || category
}

const getLevelType = (level) => {
  const map = {
    DEBUG: 'info',
    INFO: 'success',
    WARN: 'warning',
    ERROR: 'danger'
  }
  return map[level] || 'info'
}

const handleSearch = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      ...filters
    }

    if (timeRange.value && timeRange.value.length === 2) {
      params.start_time = timeRange.value[0]
      params.end_time = timeRange.value[1]
    }

    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    const res = await getLogList(params)
    if (res.success) {
      logs.value = res.logs || []
      total.value = res.total || 0
    } else {
      logs.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('查询日志失败:', error)
    ElMessage.error('查询日志失败')
    logs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  filters.category = ''
  filters.source_module = ''
  filters.user_id = ''
  timeRange.value = []
  currentPage.value = 1
  handleSearch()
}

const handleViewDetail = (row) => {
  selectedLog.value = row
  detailVisible.value = true
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.filter-card {
  margin-bottom: var(--spacing-4);
}

.table-card {
  margin-top: var(--spacing-4);
}

.pagination-wrapper {
  margin-top: var(--spacing-4);
  display: flex;
  justify-content: flex-end;
}

.log-content {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  background: var(--color-bg);
  padding: var(--spacing-3);
  border-radius: var(--radius-base);
  margin: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  :deep(.el-form-item) {
    margin-bottom: var(--spacing-4);
  }
}
</style>
