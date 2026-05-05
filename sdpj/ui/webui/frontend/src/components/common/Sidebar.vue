<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <div class="logo">
        <span class="logo-text">SDPJ-System</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-group">
        <router-link
          v-for="item in businessItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <span class="nav-text">{{ item.label }}</span>
        </router-link>
      </div>

      <div class="nav-group nav-group-management">
        <router-link
          v-for="item in managementItems"
          :key="item.path"
          :to="item.path"
          class="nav-item nav-item-management"
          :class="{ active: $route.path === item.path }"
        >
          <span class="nav-text">{{ item.label }}</span>
        </router-link>
      </div>
    </nav>

    <div class="sidebar-user">
      <div class="user-divider"></div>
      <el-dropdown @command="handleCommand" trigger="click">
        <div class="user-info">
          <div class="user-avatar">{{ userInitial }}</div>
          <span v-if="!collapsed" class="username">{{ username }}</span>
          <svg v-if="!collapsed" class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              个人信息
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store'
import { logout as apiLogout } from '../../api/auth'

defineProps({
  collapsed: { type: Boolean, default: false }
})

const router = useRouter()
const authStore = useAuthStore()

const username = computed(() => authStore.user?.username || '用户')
const userInitial = computed(() => username.value.charAt(0).toUpperCase())

const businessItems = [
  { path: '/dashboard', label: '仪表盘' },
  { path: '/detection', label: '安全检测' },
  { path: '/reports', label: '检测报告' },
  { path: '/datasets', label: '检测数据集' },
  { path: '/private-config', label: '私有配置' }
]

const managementItems = [
  { path: '/logs', label: '系统日志' },
  { path: '/dac', label: '权限管理' },
  { path: '/settings', label: '系统设置' }
]

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
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-base);
  overflow: hidden;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 16px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  width: 100%;
}

.logo-text {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: #404040;
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  padding: var(--spacing-4) var(--spacing-3);
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-group {
  display: flex;
  flex-direction: column;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  margin-bottom: 2px;
  color: #404040;
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-fast);
  position: relative;
}

.nav-item:hover {
  background: var(--color-surface-hover);
}

.nav-item.active {
  background: rgba(59, 130, 246, 0.12);
  color: rgb(59, 130, 246);
}

.nav-item-management {
  color: #404040;
}

.nav-item-management.active {
  color: rgb(59, 130, 246);
}

.nav-text {
  white-space: nowrap;
}

.sidebar-user {
  padding: 0 var(--spacing-3) var(--spacing-4);
}

.sidebar-user :deep(.el-dropdown) {
  display: block;
}

.sidebar-user :deep(.el-tooltip__trigger) {
  display: flex;
  justify-content: center;
}

.user-divider {
  height: 1px;
  background: var(--color-gray-200);
  margin-bottom: var(--spacing-3);
}

.user-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.user-info:hover {
  background: var(--color-surface-hover);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  flex-shrink: 0;
}

.username {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: #404040;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-icon {
  width: 16px;
  height: 16px;
  color: #404040;
  transition: transform var(--transition-fast);
  flex-shrink: 0;
}

.user-info:hover .dropdown-icon {
  transform: translateY(2px);
}

.menu-icon {
  width: 16px;
  height: 16px;
  color: var(--color-text-secondary);
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  font-size: var(--font-size-sm);
}

.sidebar-nav::-webkit-scrollbar {
  width: 4px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: var(--color-gray-400);
  border-radius: var(--radius-full);
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: var(--z-fixed);
    box-shadow: var(--shadow-lg);
  }

  .sidebar.collapsed {
    transform: translateX(-100%);
  }
}
</style>
