<template>
  <div class="layout-container">
    <!-- 移动端遮罩层 -->
    <transition name="backdrop-fade">
      <div
        v-if="!sidebarCollapsed && isMobile"
        class="sidebar-backdrop"
        @click="sidebarCollapsed = true"
      ></div>
    </transition>

    <Sidebar :collapsed="sidebarCollapsed" @close="sidebarCollapsed = true" />

    <div class="layout-main">
      <AppHeader />

      <main class="content-area">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from '../components/common/Sidebar.vue'
import AppHeader from '../components/common/Header.vue'
import { useSystemNotifications } from '../composables/useSystemNotifications'

const sidebarCollapsed = ref(false)
const isMobile = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (!isMobile.value) {
    sidebarCollapsed.value = false
  } else {
    sidebarCollapsed.value = true
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

useSystemNotifications()
</script>

<style scoped>
.layout-container {
  display: flex;
  height: 100vh;
  background-color: var(--color-bg);
  overflow: hidden;
  position: relative;
}

.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-6);
  background-color: var(--color-bg);
}

/* 移动端遮罩层 */
.sidebar-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: calc(var(--z-fixed) - 1);
  backdrop-filter: blur(2px);
}

.backdrop-fade-enter-active,
.backdrop-fade-leave-active {
  transition: opacity var(--transition-base);
}

.backdrop-fade-enter-from,
.backdrop-fade-leave-to {
  opacity: 0;
}

/* 页面切换动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity var(--transition-base), transform var(--transition-base);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式 */
@media (max-width: 768px) {
  .content-area {
    padding: var(--spacing-4);
  }
}
</style>
