<template>
  <PageLayout title="权限管理" description="管理用户对私有资源的访问控制">
    <el-card class="grant-card">
      <template #header>授予访问权限</template>
      <el-form :model="grantForm" inline>
        <el-form-item label="资源ID">
          <el-input-number v-model="grantForm.resource_id" :min="1" />
        </el-form-item>
        <el-form-item label="被授权用户ID">
          <el-input-number v-model="grantForm.grantee_user_id" :min="1" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="grantAccess" :loading="granting">授权</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <div class="acl-header">
          <span>访问控制列表</span>
          <div class="query-controls">
            <el-input-number v-model="queryResourceId" :min="1" size="small" />
            <el-button size="small" @click="loadAcl">查询</el-button>
          </div>
        </div>
      </template>
      <el-table :data="aclList" v-loading="loading">
        <el-table-column prop="acl_id" label="ACL ID" width="100" />
        <el-table-column prop="resource_id" label="资源ID" width="100" />
        <el-table-column prop="grantee_user_id" label="被授权用户ID" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="revokeAccess(row.acl_id)">撤销</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </PageLayout>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { dacOperation } from '../api/user'
import PageLayout from '../components/common/PageLayout.vue'

const granting = ref(false)
const loading = ref(false)
const aclList = ref([])
const queryResourceId = ref(1)

const grantForm = ref({ resource_id: 1, grantee_user_id: 1 })

const grantAccess = async () => {
  granting.value = true
  try {
    const res = await dacOperation('grant', {
      resource_id: grantForm.value.resource_id,
      grantee_user_id: grantForm.value.grantee_user_id
    })
    if (res.success) {
      ElMessage.success('授权成功')
      await loadAcl()
    } else {
      ElMessage.error(res.error || '授权失败')
    }
  } catch {
    ElMessage.error('授权失败')
  } finally {
    granting.value = false
  }
}

const loadAcl = async () => {
  loading.value = true
  try {
    const res = await dacOperation('list', { resource_id: queryResourceId.value })
    aclList.value = res.success ? (res.acl_list || []) : []
  } catch {
    aclList.value = []
  } finally {
    loading.value = false
  }
}

const revokeAccess = async (aclId) => {
  try {
    const res = await dacOperation('revoke', { acl_id: aclId })
    if (res.success) {
      ElMessage.success('已撤销')
      await loadAcl()
    } else {
      ElMessage.error(res.error || '撤销失败')
    }
  } catch {
    ElMessage.error('撤销失败')
  }
}
</script>

<style scoped>
.grant-card {
  margin-bottom: var(--spacing-6);
}

.acl-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.query-controls {
  display: flex;
  gap: var(--spacing-2);
  align-items: center;
}
</style>

<style scoped>
.dac-manager h2 { margin-bottom: 20px; }
</style>
