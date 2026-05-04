<template>
  <div class="page-layout" :style="{ maxWidth: maxWidth }">
    <div class="page-header" v-if="$slots.header || title">
      <slot name="header">
        <h1 class="page-title">{{ title }}</h1>
        <p v-if="description" class="page-description">{{ description }}</p>
      </slot>
    </div>
    <div class="page-content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  maxWidth: {
    type: String,
    default: 'var(--container-max-width)'
  }
})
</script>

<style scoped>
.page-layout {
  margin: 0 auto;
  padding: var(--spacing-8);
}

.page-header {
  margin-bottom: var(--spacing-8);
}

.page-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  margin: 0 0 var(--spacing-2) 0;
}

.page-description {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  margin: 0;
}

.page-content {
  /* 内容区域由子组件控制 */
}
</style>
