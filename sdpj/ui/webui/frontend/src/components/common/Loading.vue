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
  padding: var(--spacing-10) 0;
}

.loading-icon {
  animation: rotate 1.5s linear infinite;
  color: var(--color-primary);
}

.loading-text {
  margin-top: var(--spacing-3);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
