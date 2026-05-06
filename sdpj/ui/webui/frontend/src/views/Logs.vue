<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">系统日志</h1>
      <p class="page-info">查看系统运行日志和操作记录</p>

      <!-- 筛选条件显示区域 -->
      <div class="filters-display" v-if="hasActiveFilters">
        <span class="filter-label">当前筛选：</span>
        <el-tag
          v-for="level in selectedLevels"
          :key="'level-' + level"
          closable
          @close="removeLevelFilter(level)"
          type="info"
          class="filter-tag"
        >
          级别: {{ level.toUpperCase() }}
        </el-tag>
        <el-tag
          v-for="module in selectedModules"
          :key="'module-' + module"
          closable
          @close="removeModuleFilter(module)"
          type="info"
          class="filter-tag"
        >
          模块: {{ module }}
        </el-tag>
        <el-tag
          v-for="user in selectedUsers"
          :key="'user-' + user"
          closable
          @close="removeUserFilter(user)"
          type="info"
          class="filter-tag"
        >
          用户: {{ user }}
        </el-tag>
        <el-button size="small" text @click="clearAllFilters">清除全部</el-button>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th style="width: 16%">
                <div class="th-content">
                  <span>时间</span>
                </div>
              </th>
              <th style="width: 10%">
                <div class="th-content">
                  <span>级别</span>
                  <el-popover placement="bottom" :width="200" trigger="click">
                    <template #reference>
                      <span class="filter-icon">▼</span>
                    </template>
                    <div class="filter-checkboxes">
                      <el-checkbox-group v-model="selectedLevels" @change="handleLevelFilterChange">
                        <el-checkbox label="info">INFO</el-checkbox>
                        <el-checkbox label="warn">WARNING</el-checkbox>
                        <el-checkbox label="error">ERROR</el-checkbox>
                        <el-checkbox label="debug">DEBUG</el-checkbox>
                      </el-checkbox-group>
                    </div>
                  </el-popover>
                </div>
              </th>
              <th style="width: 12%">
                <div class="th-content">
                  <span>模块</span>
                  <el-popover placement="bottom" :width="200" trigger="click">
                    <template #reference>
                      <span class="filter-icon">▼</span>
                    </template>
                    <div class="filter-checkboxes">
                      <el-checkbox-group v-model="selectedModules" @change="handleModuleFilterChange">
                        <el-checkbox label="StateScheduler">StateScheduler</el-checkbox>
                        <el-checkbox label="DataProcessor">DataProcessor</el-checkbox>
                        <el-checkbox label="UserCenter">UserCenter</el-checkbox>
                        <el-checkbox label="LLMRegistry">LLMRegistry</el-checkbox>
                      </el-checkbox-group>
                    </div>
                  </el-popover>
                </div>
              </th>
              <th style="width: 12%">
                <div class="th-content">
                  <span>用户</span>
                  <el-popover placement="bottom" :width="200" trigger="click">
                    <template #reference>
                      <span class="filter-icon">▼</span>
                    </template>
                    <div class="filter-checkboxes">
                      <el-checkbox-group v-model="selectedUsers" @change="handleUserFilterChange">
                        <el-checkbox label="SDPJ-System">SDPJ-System</el-checkbox>
                        <el-checkbox :label="String(u)" v-for="u in uniqueUsers" :key="u">{{ u }}</el-checkbox>
                      </el-checkbox-group>
                    </div>
                  </el-popover>
                </div>
              </th>
              <th style="width: 50%">
                <div class="th-content">
                  <span>内容</span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody v-if="logs.length > 0">
            <tr v-for="log in logs" :key="log.log_id">
              <td>{{ formatTime(log.timestamp) }}</td>
              <td>
                <span class="level-tag" :class="`level-${(log.level || 'info').toLowerCase()}`">
                  {{ log.level || 'INFO' }}
                </span>
              </td>
              <td>{{ log.source_module || '-' }}</td>
              <td>
                <span v-if="log.username && log.username !== 'SDPJ-System'" class="user-tag">
                  {{ log.username }}
                </span>
                <span v-else class="system-tag">SDPJ-System</span>
              </td>
              <td>{{ log.description || '-' }}</td>
            </tr>
          </tbody>
          <tbody v-else-if="!loading && logs.length === 0">
            <tr>
              <td colspan="5" class="empty-row"><div class="empty-center" style="margin-right: 46%;">暂无日志</div></td>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const logs = ref([])
const loading = ref(true)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const uniqueUsers = ref([])

const selectedLevels = ref([])
const selectedModules = ref([])
const selectedUsers = ref([])

const formatTime = (ts) => {
  if (!ts) return '-'
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ts
    const pad = (n) => String(n).padStart(2, '0')
    const Y = d.getFullYear()
    const M = pad(d.getMonth() + 1)
    const D = pad(d.getDate())
    const h = pad(d.getHours())
    const m = pad(d.getMinutes())
    const s = pad(d.getSeconds())
    return `${Y}-${M}-${D} ${h}:${m}:${s}`
  } catch {
    return ts
  }
}

const hasActiveFilters = computed(() => {
  return selectedLevels.value.length > 0 || selectedModules.value.length > 0 || selectedUsers.value.length > 0
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (selectedLevels.value.length === 1) {
      params.level = selectedLevels.value[0]
    }
    if (selectedModules.value.length === 1) {
      params.source_module = selectedModules.value[0]
    }
    if (selectedUsers.value.length === 1) {
      params.user_id = selectedUsers.value[0]
    }

    const res = await api.get('/logs', { params })
    if (res.success) {
      logs.value = res.data?.logs || []
      total.value = res.data?.total || 0
    }
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const fetchUniqueUsers = async () => {
  try {
    const res = await api.get('/logs/users')
    if (res.success) {
      uniqueUsers.value = res.data?.users || []
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

const handleLevelFilterChange = () => {
  currentPage.value = 1
  fetchLogs()
}

const handleModuleFilterChange = () => {
  currentPage.value = 1
  fetchLogs()
}

const handleUserFilterChange = () => {
  currentPage.value = 1
  fetchLogs()
}

const removeLevelFilter = (level) => {
  selectedLevels.value = selectedLevels.value.filter(l => l !== level)
  currentPage.value = 1
  fetchLogs()
}

const removeModuleFilter = (module) => {
  selectedModules.value = selectedModules.value.filter(m => m !== module)
  currentPage.value = 1
  fetchLogs()
}

const removeUserFilter = (user) => {
  selectedUsers.value = selectedUsers.value.filter(u => u !== user)
  currentPage.value = 1
  fetchLogs()
}

const clearAllFilters = () => {
  selectedLevels.value = []
  selectedModules.value = []
  selectedUsers.value = []
  currentPage.value = 1
  fetchLogs()
}

let ws = null
let wsReconnectTimer = null

function connectLogWs() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${proto}://${location.host}/ws/logs`)

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    if (msg.type === 'log') {
      const newLog = msg.data
      const passesLevel = selectedLevels.value.length === 0 || selectedLevels.value.includes(newLog.level?.toLowerCase())
      const passesModule = selectedModules.value.length === 0 || selectedModules.value.includes(newLog.source_module)
      const username = newLog.username || 'SDPJ-System'
      const passesUser = selectedUsers.value.length === 0 || selectedUsers.value.includes(username)
      if (passesLevel && passesModule && passesUser) {
        total.value += 1
        if (currentPage.value === 1) {
          logs.value.unshift(newLog)
          if (logs.value.length > pageSize.value) {
            logs.value.pop()
          }
        }
      }
    }
  }

  ws.onclose = () => {
    wsReconnectTimer = setTimeout(connectLogWs, 5000)
  }

  ws.onerror = () => {
    ws.close()
  }
}

onMounted(() => {
  fetchUniqueUsers()
  fetchLogs()
  connectLogWs()
})

onUnmounted(() => {
  if (wsReconnectTimer) {
    clearTimeout(wsReconnectTimer)
    wsReconnectTimer = null
  }
  if (ws) {
    ws.onclose = null
    ws.close()
    ws = null
  }
})
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

.th-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.filter-icon {
  cursor: pointer;
  font-size: 10px;
  color: #8b8b8b;
  user-select: none;
  padding: 2px 4px;
  border-radius: 3px;
  transition: all 0.2s;
}

.filter-icon:hover {
  background: #e5e5e5;
  color: #404040;
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

.level-warn {
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

.user-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
  font-family: var(--font-family-mono);
}

.system-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(100, 116, 139, 0.12);
  color: #475569;
  font-family: var(--font-family-mono);
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

.pagination-wrapper {
  display: flex;
  justify-content: center;
}

.filters-display {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 8px;
}

.filter-label {
  font-size: 14px;
  color: #8b8b8b;
  font-weight: 500;
}

.filter-tag {
  font-size: 13px;
}

.filter-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-checkboxes :deep(.el-checkbox) {
  margin-right: 0;
  height: auto;
}

.filter-checkboxes :deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
