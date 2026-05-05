<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">检测报告</h1>
      <p class="page-info">查看和管理所有安全检测生成的合规性报告</p>
      <ReportTable />
    </div>
  </div>
</template>

<script setup>
import ReportTable from '../components/report/ReportTable.vue'
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
