<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">系统日志</h1>
      <p class="page-info">查看系统运行日志和操作记录</p>

      <div class="table-wrapper" v-loading="loading">
        <table>
          <thead>
            <tr>
              <th style="width: 18%">时间</th>
              <th style="width: 12%">级别</th>
              <th style="width: 15%">模块</th>
              <th style="width: 55%">内容</th>
            </tr>
          </thead>
          <tbody v-if="logs.length > 0">
            <tr v-for="(log, idx) in logs" :key="idx">
              <td>{{ log.timestamp || log.time || '-' }}</td>
              <td>
                <span class="level-tag" :class="`level-${(log.level || 'info').toLowerCase()}`">
                  {{ log.level || 'INFO' }}
                </span>
              </td>
              <td>{{ log.module || '-' }}</td>
              <td>{{ log.message || log.content || '-' }}</td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="99" class="empty-row">暂无日志</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination-wrapper" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="fetchLogs"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const logs = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await api.get('/logs', { params: { page: currentPage.value, page_size: pageSize.value } })
    if (res.success) {
      logs.value = res.logs || []
      total.value = res.total || 0
    }
  } catch { logs.value = [] }
  finally { loading.value = false }
}

onMounted(fetchLogs)
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

.level-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
}

.level-info {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
}

.level-warning {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.level-error {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.level-debug {
  background: #f5f5f5;
  color: #8b8b8b;
}

.empty-row {
  padding: 24px 8px;
  text-align: center;
  color: #8b8b8b;
  font-size: 13px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
}
</style>
