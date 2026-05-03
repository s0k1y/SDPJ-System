<template>
  <div>
    <h2>可用检测数据集</h2>
    <el-table :data="datasets" v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="risk_type" label="风险类型" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDatasets } from '../api/detection'

const loading = ref(false)
const datasets = ref([])

onMounted(async () => {
  loading.value = true
  try {
    const res = await getDatasets()
    datasets.value = Array.isArray(res) ? res : (res.datasets || [])
  } finally {
    loading.value = false
  }
})
</script>
