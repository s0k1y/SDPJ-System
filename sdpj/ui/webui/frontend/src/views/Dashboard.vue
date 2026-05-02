<template>
  <div class="dashboard">
    <h2>仪表盘</h2>
    
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <el-statistic title="总检测任务" :value="stats.totalTasks" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="合规任务" :value="stats.compliantTasks" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="违规任务" :value="stats.nonCompliantTasks" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="合规率" :value="stats.complianceRate" suffix="%" />
        </el-card>
      </el-col>
    </el-row>
    
    <el-card style="margin-top: 20px">
      <h3>最近任务</h3>
      <el-table :data="recentTasks" style="width: 100%">
        <el-table-column prop="task_id" label="任务ID" width="200" />
        <el-table-column prop="model_id" label="模型" />
        <el-table-column prop="dataset_id" label="数据集" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : 'info'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const stats = ref({
  totalTasks: 0,
  compliantTasks: 0,
  nonCompliantTasks: 0,
  complianceRate: 0
})

const recentTasks = ref([])

onMounted(async () => {
  try {
    const res = await api.get('/status')
    // 模拟数据
    stats.value = {
      totalTasks: 156,
      compliantTasks: 142,
      nonCompliantTasks: 14,
      complianceRate: 91.0
    }
  } catch (error) {
    console.error(error)
  }
})
</script>

<style scoped>
.dashboard h2 {
  margin-bottom: 20px;
}

.dashboard h3 {
  margin-bottom: 15px;
}
</style>
