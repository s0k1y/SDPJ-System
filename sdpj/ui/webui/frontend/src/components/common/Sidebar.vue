<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <div class="logo">
        <span class="logo-text">SDPJ-System</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      <!-- 业务组 -->
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

      <!-- 分隔线 -->
      <div class="nav-divider"></div>

      <!-- 管理组 -->
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

    <div class="sidebar-footer">
      <div class="footer-divider"></div>
      <div class="footer-content">
        <span v-if="!collapsed" class="footer-text">v1.0.0</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  collapsed: { type: Boolean, default: false }
})

// 业务组导航
const businessItems = [
  { path: '/dashboard', label: '仪表盘' },
  { path: '/detection', label: '安全检测' },
  { path: '/reports', label: '检测报告' },
  { path: '/datasets', label: '检测数据集' },
  { path: '/private-config', label: '私有配置' }
]

// 管理组导航
const managementItems = [
  { path: '/logs', label: '系统日志' },
  { path: '/dac', label: '权限管理' },
  { path: '/settings', label: '系统设置' }
]
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-base);
  overflow: hidden;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

/* 侧边栏头部 */
.sidebar-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  width: 100%;
}

.logo-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  border-radius: var(--radius-base);
  color: white;
  flex-shrink: 0;
}

.logo-icon svg {
  width: 20px;
  height: 20px;
}

.logo-text {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  white-space: nowrap;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  padding: var(--spacing-4) var(--spacing-3);
  overflow-y: auto;
  overflow-x: hidden;
}

/* 导航分组 */
.nav-group {
  display: flex;
  flex-direction: column;
}

/* 分隔线 */
.nav-divider {
  height: 1px;
  background: var(--color-border);
  margin: var(--spacing-4) var(--spacing-4);
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  margin-bottom: var(--spacing-2);
  border-radius: var(--radius-base);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;
}

.nav-item:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.nav-item.active {
  background: var(--color-primary-lighter);
  color: var(--color-primary-dark);
}

/* 管理组导航项 - 降低视觉权重 */
.nav-item-management {
  color: var(--color-text-tertiary);
}

.nav-item-management:hover {
  color: var(--color-text-secondary);
}

.nav-item-management.active {
  color: var(--color-primary-dark);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: var(--color-primary);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-text {
  white-space: nowrap;
}

/* 底部 */
.sidebar-footer {
  padding: var(--spacing-4) var(--spacing-3);
}

.footer-divider {
  height: 1px;
  background: var(--color-border);
  margin-bottom: var(--spacing-3);
}

.footer-content {
  padding: 0 var(--spacing-4);
}

.footer-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

/* 动画 */
.logo-fade-enter-active,
.logo-fade-leave-active,
.text-fade-enter-active,
.text-fade-leave-active {
  transition: opacity var(--transition-fast);
}

.logo-fade-enter-from,
.logo-fade-leave-to,
.text-fade-enter-from,
.text-fade-leave-to {
  opacity: 0;
}

/* 滚动条 */
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

/* 响应式 */
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
