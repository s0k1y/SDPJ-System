<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">安全检测</h1>
      <p class="page-info">配置检测参数并启动大语言模型安全风险检测任务</p>
      <DetectionForm @start="$emit('startDetection', $event)" />
    </div>
  </div>
</template>

<script setup>
import DetectionForm from '../components/detection/DetectionForm.vue'
</script>

<style scoped>
.page-container {
  width: 100%;
}

.page-inner {
  max-width: 936px;
  margin: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #404040;
  line-height: 32px;
  margin: 0 0 32px;
}

.page-info {
  font-size: 14px;
  color: #404040;
  line-height: 25px;
  margin: 0 0 22px;
}
</style>
