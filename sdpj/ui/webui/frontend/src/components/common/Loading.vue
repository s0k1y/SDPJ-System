<template>
  <div class="loading-container" v-if="visible">
    <template v-if="variant === 'spinner'">
      <el-icon class="loading-icon" :size="size"><Loading /></el-icon>
      <span v-if="text" class="loading-text">{{ text }}</span>
    </template>

    <template v-else-if="variant === 'text'">
      <div v-for="n in textRows" :key="n" class="shimmer-line" :style="{ width: textWidths[(n - 1) % textWidths.length] }"></div>
    </template>

    <template v-else-if="variant === 'card'">
      <div v-for="n in cardCount" :key="n" class="shimmer-card">
        <div class="shimmer-line shimmer-card-title" style="width: 60%"></div>
        <div class="shimmer-line shimmer-card-body" style="width: 90%"></div>
        <div class="shimmer-line shimmer-card-body" style="width: 75%"></div>
      </div>
    </template>

    <template v-else-if="variant === 'table'">
      <div v-for="n in tableRows" :key="n" class="shimmer-table-row">
        <div v-for="c in tableCols" :key="c" class="shimmer-cell" :style="{ width: colWidths[(c - 1) % colWidths.length] || 'auto' }">
          <div class="shimmer-line" style="width: 100%"></div>
        </div>
      </div>
    </template>

    <template v-else-if="variant === 'detail'">
      <div class="shimmer-detail">
        <div class="shimmer-line shimmer-detail-title" style="width: 40%"></div>
        <div v-for="n in detailRows" :key="n" class="shimmer-detail-row">
          <div class="shimmer-line shimmer-detail-label" style="width: 20%"></div>
          <div class="shimmer-line shimmer-detail-value" :style="{ width: detailValueWidths[(n - 1) % detailValueWidths.length] }"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { Loading } from '@element-plus/icons-vue'

defineProps({
  visible: { type: Boolean, default: true },
  variant: { type: String, default: 'spinner' },
  text: { type: String, default: '' },
  size: { type: Number, default: 32 },
  textRows: { type: Number, default: 1 },
  textWidths: { type: Array, default: () => ['100%'] },
  cardCount: { type: Number, default: 1 },
  tableRows: { type: Number, default: 1 },
  tableCols: { type: Number, default: 4 },
  colWidths: { type: Array, default: () => [] },
  detailRows: { type: Number, default: 1 },
  detailValueWidths: { type: Array, default: () => ['55%'] }
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

.shimmer-line {
  height: 16px;
  border-radius: 6px;
  background: linear-gradient(
    100deg,
    var(--shimmer-color-base) 40%,
    var(--shimmer-color-highlight) 50%,
    var(--shimmer-color-base) 60%
  );
  background-size: 200% 100%;
  animation: shimmer var(--shimmer-duration) ease-in-out infinite;
}

.shimmer-card {
  padding: var(--spacing-6) 0;
  border-bottom: 1px solid var(--color-gray-100);
}

.shimmer-card-title {
  height: 20px;
  margin-bottom: var(--spacing-3);
  border-radius: 6px;
}

.shimmer-card-body {
  margin-bottom: var(--spacing-2);
}

.shimmer-table-row {
  display: flex;
  gap: var(--spacing-4);
  padding: 12px 0;
  border-bottom: 1px solid var(--color-gray-100);
}

.shimmer-cell {
  flex: 1;
}

.shimmer-detail-title {
  height: 24px;
  margin-bottom: var(--spacing-8);
  border-radius: 6px;
}

.shimmer-detail-row {
  display: flex;
  gap: var(--spacing-8);
  padding: 14px 0;
  border-bottom: 1px solid var(--color-gray-100);
  align-items: center;
}

.shimmer-detail-label {
  height: 16px;
  flex-shrink: 0;
}

.shimmer-detail-value {
  height: 16px;
}
</style>
