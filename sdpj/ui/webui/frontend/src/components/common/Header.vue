<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-icon class="collapse-btn" @click="$emit('toggle-sidebar')">
        <Fold v-if="!collapsed" />
        <Expand v-else />
      </el-icon>
    </div>
    <div class="header-right">
      <el-dropdown @command="handleCommand">
        <span class="user-info">
          <el-icon><User /></el-icon>
          <span class="username">{{ username }}</span>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人信息</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { User, Fold, Expand } from '@element-plus/icons-vue'
import { useAuthStore } from '../../store'
import { logout as apiLogout } from '../../api/auth'

defineProps({
  collapsed: { type: Boolean, default: false }
})

defineEmits(['toggle-sidebar'])

const router = useRouter()
const authStore = useAuthStore()

const username = computed(() => authStore.user?.username || '用户')

const handleCommand = async (command) => {
  if (command === 'logout') {
    await apiLogout().catch(() => {})
    authStore.logout()
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/settings')
  }
}
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  padding: 0 20px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}

.collapse-btn:hover {
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
}

.username {
  font-size: 14px;
}
</style>