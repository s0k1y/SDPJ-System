<template>
  <el-container class="layout-container">
    <el-aside :width="sidebarCollapsed ? '64px' : '200px'">
      <Sidebar :collapsed="sidebarCollapsed" />
    </el-aside>

    <el-container>
      <AppHeader :collapsed="sidebarCollapsed" @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed" />

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from '../components/common/Sidebar.vue'
import AppHeader from '../components/common/Header.vue'
import { useSystemNotifications } from '../composables/useSystemNotifications'

const sidebarCollapsed = ref(false)
useSystemNotifications()
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
