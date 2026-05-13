<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">新建检测任务</h1>
      <div class="breadcrumb">
        <template v-for="(item, i) in crumbItems" :key="i">
          <span v-if="i > 0" class="crumb-sep">/</span>
          <div
            class="crumb"
            :class="{
              active: step === i,
              done: step > i,
              clickable: step > i
            }"
            @click="goToStep(i)"
          >
            <span class="crumb-dot"></span>
            <span class="crumb-text">{{ item }}</span>
          </div>
        </template>
      </div>
      <DetectionForm ref="formRef" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import DetectionForm from '../components/detection/DetectionForm.vue'

const crumbItems = ['配置被测大模型', '配置被测数据集与检测参数', '确认启动']

const formRef = ref(null)
const step = computed(() => formRef.value?.currentStep ?? 0)

function goToStep(s) {
  if (s < step.value) {
    formRef.value.currentStep = s
  }
}
</script>

<style scoped>
.breadcrumb {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 14px;
  border-bottom: 1px solid #e5e5e5;
  font-size: 13px;
}

.crumb {
  display: flex;
  align-items: center;
  gap: 6px;
}

.crumb-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #d9d9d9;
  transition: all 200ms;
}

.crumb.active .crumb-dot {
  background: rgb(59, 130, 246);
  width: 8px;
  height: 8px;
}

.crumb-text {
  color: #999;
  font-weight: 500;
  transition: color 200ms;
}

.crumb.active .crumb-text {
  color: #1a1a1a;
  font-weight: 600;
}

.crumb.done .crumb-dot {
  background: #10B981;
}

.crumb.done .crumb-text {
  color: #666;
}

.crumb.clickable {
  cursor: pointer;
}

.crumb.clickable:hover .crumb-text {
  color: #404040;
}

.crumb-sep {
  margin: 0 10px;
  color: #d9d9d9;
  font-size: 12px;
}

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

</style>
