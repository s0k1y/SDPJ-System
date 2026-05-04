<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import { onMounted } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { useThemeStore } from './store/theme'

// 初始化主题
const themeStore = useThemeStore()

onMounted(() => {
  // 确保主题在应用启动时正确应用
  document.documentElement.setAttribute('data-theme', themeStore.theme)
})
</script>

<style>
/* 引入设计令牌 */
@import './styles/design-tokens.css';

/* 引入全局样式 */
@import './styles/global.scss';
</style>
