<template>
  <div class="loading-container" v-if="visible">
    <el-icon class="loading-icon" :size="size"><Loading /></el-icon>
    <span v-if="text" class="loading-text">{{ text }}</span>
  </div>
</template>

<script setup>
import { Loading } from '@element-plus/icons-vue'

defineProps({
  visible: { type: Boolean, default: true },
  text: { type: String, default: '加载中...' },
  size: { type: Number, default: 32 }
})
</script>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.loading-icon {
  animation: rotate 1.5s linear infinite;
  color: #409eff;
}

.loading-text {
  margin-top: 12px;
  color: #909399;
  font-size: 14px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
