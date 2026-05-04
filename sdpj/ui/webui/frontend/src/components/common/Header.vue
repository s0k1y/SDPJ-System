<template>
  <header class="app-header">
    <div class="header-left">
    </div>

    <div class="header-center">
      <transition name="indicator-fade">
        <div v-if="hasActive" class="task-indicator" @click="goToDetection">
          <span class="pulse-dot"></span>
          <span class="indicator-text">
            {{ runningCount > 0 ? `${runningCount} 个任务运行中` : `${pendingCount} 个任务等待中` }}
          </span>
        </div>
      </transition>
    </div>

    <div class="header-right">
      <el-dropdown @command="handleCommand" trigger="click">
        <div class="user-info">
          <div class="user-avatar">
            {{ userInitial }}
          </div>
          <span class="username">{{ username }}</span>
          <svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store'
import { logout as apiLogout } from '../../api/auth'
import { useRunningTasks } from '../../composables/useRunningTasks'

const router = useRouter()
const authStore = useAuthStore()
const { runningCount, pendingCount, hasActive } = useRunningTasks()

const username = computed(() => authStore.user?.username || '用户')
const userInitial = computed(() => username.value.charAt(0).toUpperCase())

const goToDetection = () => {
  router.push('/detection')
}

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
  height: var(--header-height);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 var(--spacing-6);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.task-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-1) var(--spacing-4);
  border-radius: var(--radius-full);
  background: var(--color-primary-lighter);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.task-indicator:hover {
  background: var(--color-primary-light);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.indicator-text {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary-dark);
  white-space: nowrap;
}

.indicator-fade-enter-active,
.indicator-fade-leave-active {
  transition: opacity var(--transition-base), transform var(--transition-base);
}

.indicator-fade-enter-from,
.indicator-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-base);
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
}

.username {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

.dropdown-icon {
  width: 16px;
  height: 16px;
  color: var(--color-text-secondary);
  transition: transform var(--transition-fast);
}

.user-info:hover .dropdown-icon {
  transform: translateY(2px);
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  font-size: var(--font-size-sm);
}

.menu-icon {
  width: 16px;
  height: 16px;
  color: var(--color-text-secondary);
}

@media (max-width: 768px) {
  .app-header {
    padding: 0 var(--spacing-4);
  }

  .username {
    display: none;
  }
}
</style>
