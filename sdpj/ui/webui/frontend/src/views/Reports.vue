<template>
  <div class="reports">
    <h2>检测报告</h2>
    
    <el-card>
      <el-table :data="reports" style="width: 100%">
        <el-table-column prop="report_id" label="报告ID" width="100" />
        <el-table-column prop="task_id" label="任务ID" width="200" />
        <el-table-column prop="model_id" label="模型" />
        <el-table-column prop="risk_level" label="风险等级">
          <template #default="{ row }">
            <el-tag :type="getRiskType(row.risk_level)">
              {{ row.risk_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="compliance_rate" label="合规率" />
        <el-table-column prop="created_at" label="生成时间" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="viewReport(row)">查看</el-button>
            <el-button size="small" type="primary" @click="downloadReport(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const reports = ref([])

const getRiskType = (level) => {
  const map = { '低': 'success', '中': 'warning', '高': 'danger' }
  return map[level] || 'info'
}

const viewReport = (row) => {
  ElMessage.info('查看报告: ' + row.report_id)
}

const downloadReport = (row) => {
  ElMessage.success('下载报告: ' + row.report_id)
}

onMounted(async () => {
  // 模拟数据
  reports.value = [
    {
      report_id: 1,
      task_id: 'task-001',
      model_id: 'gpt-4',
      risk_level: '低',
      compliance_rate: '95%',
      created_at: '2026-05-03 10:00:00'
    }
  ]
})
</script>

<style scoped>
.reports h2 {
  margin-bottom: 20px;
}
</style>
