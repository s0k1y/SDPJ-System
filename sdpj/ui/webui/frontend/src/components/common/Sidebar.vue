<template>
  <div class="sidebar" :class="{ collapsed }">
    <div class="logo">
      <span v-if="!collapsed">SDPJ-System</span>
      <span v-else>SP</span>
    </div>
    <el-menu
      :default-active="$route.path"
      :collapse="collapsed"
      router
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409eff"
    >
      <el-menu-item index="/dashboard">
        <el-icon><Odometer /></el-icon>
        <template #title>仪表盘</template>
      </el-menu-item>
      <el-menu-item index="/detection">
        <el-icon><Search /></el-icon>
        <template #title>安全检测</template>
      </el-menu-item>
      <el-menu-item index="/reports">
        <el-icon><Document /></el-icon>
        <template #title>检测报告</template>
      </el-menu-item>
      <el-menu-item index="/datasets">
        <el-icon><DataBoard /></el-icon>
        <template #title>检测数据集</template>
      </el-menu-item>
      <el-menu-item index="/private-config">
        <el-icon><Files /></el-icon>
        <template #title>私有配置</template>
      </el-menu-item>
      <el-menu-item index="/settings">
        <el-icon><Setting /></el-icon>
        <template #title>系统设置</template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { Odometer, Search, Document, Setting, Files, DataBoard } from '@element-plus/icons-vue'

defineProps({
  collapsed: { type: Boolean, default: false }
})
</script>

<style scoped>
.sidebar {
  height: 100vh;
  background-color: #304156;
  transition: width 0.3s;
  width: 200px;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  color: #fff;
  background-color: #1f2d3d;
  white-space: nowrap;
  overflow: hidden;
}

.el-menu {
  border-right: none;
}
</style>
