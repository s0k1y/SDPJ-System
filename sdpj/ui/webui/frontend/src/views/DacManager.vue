<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">权限管理</h1>
      <p class="page-info">管理用户访问权限和角色分配</p>

      <div class="table-wrapper" v-loading="loading">
        <table>
          <thead>
            <tr>
              <th style="width: 15%">用户ID</th>
              <th style="width: 25%">用户名</th>
              <th style="width: 20%">角色</th>
              <th style="width: 20%">创建时间</th>
              <th style="width: 20%">操作</th>
            </tr>
          </thead>
          <tbody v-if="users.length > 0">
            <tr v-for="user in users" :key="user._id || user.id">
              <td><span class="cell-mono">{{ user._id || user.id }}</span></td>
              <td>{{ user.username || '-' }}</td>
              <td>
                <span class="role-tag" :class="`role-${user.role || 'user'}`">
                  {{ roleText(user.role) }}
                </span>
              </td>
              <td>{{ user.created_at || '-' }}</td>
              <td>
                <div class="action-btns">
                  <el-button class="action-btn" size="small" @click="editUser(user)">编辑</el-button>
                  <el-button class="action-btn action-btn-danger" size="small" @click="deleteUser(user)">删除</el-button>
                </div>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="99" class="empty-row">暂无用户</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const users = ref([])
const loading = ref(false)

const roleText = (role) => {
  const map = { admin: '管理员', user: '用户', viewer: '只读' }
  return map[role] || role || '用户'
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await api.get('/dac/users')
    if (res.success) users.value = res.users || []
  } catch { users.value = [] }
  finally { loading.value = false }
}

const editUser = (user) => {
  ElMessage.info(`编辑: ${user.username}`)
}

const deleteUser = async (user) => {
  await ElMessageBox.confirm(`确认删除用户 ${user.username}？`, '提示', { type: 'warning' })
  try {
    await api.delete(`/dac/users/${user._id || user.id}`)
    ElMessage.success('已删除')
    fetchUsers()
  } catch { ElMessage.error('删除失败') }
}

onMounted(fetchUsers)
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

.role-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
}

.role-admin {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.role-user {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
}

.role-viewer {
  background: #f5f5f5;
  color: #8b8b8b;
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
