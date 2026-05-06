<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">权限管理</h1>
      <p class="page-info">管理私有资源的访问权限，授予或移除其他用户的读权限</p>

      <div class="dac-layout">
        <div class="dac-left">
          <div class="section-title">我的私有资源</div>
          <div class="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th style="width: 30%">资源名称</th>
                  <th style="width: 20%">资源类型</th>
                  <th style="width: 20%">创建时间</th>
                  <th style="width: 30%; text-align: left; height: 52px; box-sizing: border-box; vertical-align: middle;">操作</th>
                </tr>
              </thead>
              <tbody v-if="resourcesLoading"></tbody>
              <tbody v-else-if="resources.length > 0">
                <tr v-for="r in resources" :key="r.resource_id" :class="{ 'row-selected': selectedResource?.resource_id === r.resource_id }">
                  <td>{{ getResourceDisplayName(r) }}</td>
                  <td>{{ r.resource_type || '-' }}</td>
                  <td>{{ formatDateTime(r.created_at) }}</td>
                  <td style="text-align: left; height: 52px; box-sizing: border-box;">
                    <div class="action-btns">
                      <el-button class="action-btn" size="small" @click="selectResource(r)">查看授权</el-button>
                      <el-button class="action-btn" size="small" @click="openGrantDialogForResource(r)">授权</el-button>
                    </div>
                  </td>
                </tr>
              </tbody>
              <tbody v-else>
                <tr><td colspan="99" class="empty-row"><div class="empty-center" style="margin-right: 26%;">暂无私有资源</div></td></tr>
              </tbody>
            </table>
          </div>

          <div class="section-title" style="margin-top: 28px;">我被授权的资源</div>
          <div class="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th style="width: 30%">资源名称</th>
                  <th style="width: 20%">资源类型</th>
                  <th style="width: 20%">所有者ID</th>
                  <th style="width: 30%">创建时间</th>
                </tr>
              </thead>
              <tbody v-if="sharedResourcesLoading"></tbody>
              <tbody v-else-if="sharedResources.length > 0">
                <tr v-for="r in sharedResources" :key="r.resource_id">
                  <td>{{ getResourceDisplayName(r) }}</td>
                  <td>{{ r.resource_type || '-' }}</td>
                  <td><span class="cell-mono">{{ r.owner_username || r.owner_user_id }}</span></td>
                  <td>{{ formatDateTime(r.created_at) }}</td>
                </tr>
              </tbody>
              <tbody v-else>
                <tr><td colspan="99" class="empty-row"><div class="empty-center" style="margin-right: 24%;">暂无被授权的资源</div></td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="dac-right" v-if="selectedResource">
          <div class="section-title">
            授权清单 — {{ getResourceDisplayName(selectedResource) }}
          </div>
          <div class="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th style="width: 25%">访问控制项ID</th>
                  <th style="width: 30%">被授权用户名</th>
                  <th style="width: 25%">授权时间</th>
                  <th style="width: 20%; text-align: left; height: 52px; box-sizing: border-box; vertical-align: middle;">操作</th>
                </tr>
              </thead>
              <tbody v-if="aclLoading"></tbody>
              <tbody v-else-if="aclList.length > 0">
                <tr v-for="acl in aclList" :key="acl.acl_id">
                  <td><span class="cell-mono">{{ acl.acl_id }}</span></td>
                  <td><span class="cell-mono">{{ acl.grantee_username || acl.grantee_user_id }}</span></td>
                  <td>{{ formatDateTime(acl.created_at) }}</td>
                  <td style="text-align: left; height: 52px; box-sizing: border-box;">
                    <div class="action-btns">
                      <el-button class="action-btn action-btn-danger" size="small" @click="revokeAccess(acl)">移除</el-button>
                    </div>
                  </td>
                </tr>
              </tbody>
              <tbody v-else>
                <tr><td colspan="99" class="empty-row"><div class="empty-center" style="margin-right: 39%;">{{ selectedResource ? '暂无授权记录' : '请选择一个资源查看授权清单' }}</div></td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="grantDialogVisible" title="授予访问权" width="400px">
      <el-form label-width="100px">
        <el-form-item label="资源名称">
          <el-input :model-value="getResourceDisplayName(selectedResource)" disabled />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="grantTargetUsername" placeholder="输入用户名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="grantDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="grantAccess" :loading="grantSaving">确认授权</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getResources, dacOperation, checkDacAccess } from '../api/user'

const resources = ref([])
const sharedResources = ref([])
const resourcesLoading = ref(true)
const sharedResourcesLoading = ref(true)
const selectedResource = ref(null)
const aclList = ref([])
const aclLoading = ref(true)

const grantDialogVisible = ref(false)
const grantTargetUsername = ref(null)
const grantSaving = ref(false)

const checkResourceId = ref(null)
const checkResult = ref(null)
const checkLoading = ref(false)

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  const d = new Date(datetime)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const getResourceDisplayName = (resource) => {
  if (!resource) return '-'
  if (resource.resource_type === 'private_config') {
    return resource.model_id || '-'
  }
  if (resource.dataset_name) {
    const parts = resource.dataset_name.split('/')
    return parts[parts.length - 1] || resource.dataset_name
  }
  return '-'
}

const fetchResources = async () => {
  resourcesLoading.value = true
  sharedResourcesLoading.value = true
  try {
    const res = await getResources()
    if (res.success) {
      resources.value = res.data?.resources || []
      sharedResources.value = res.data?.shared_resources || []
    }
  } catch { resources.value = []; sharedResources.value = [] }
  finally { resourcesLoading.value = false; sharedResourcesLoading.value = false }
}

const selectResource = (resource) => {
  selectedResource.value = resource
  fetchAclList()
}

const fetchAclList = async () => {
  if (!selectedResource.value) return
  aclLoading.value = true
  try {
    const res = await dacOperation('list', { resource_id: selectedResource.value.resource_id })
    if (res.success) {
      aclList.value = res.data?.acl_list || []
    } else {
      aclList.value = []
      ElMessage.error(res.message || '查询授权清单失败')
    }
  } catch { aclList.value = [] }
  finally { aclLoading.value = false }
}

const openGrantDialog = () => {
  grantTargetUsername.value = null
  grantDialogVisible.value = true
}

const openGrantDialogForResource = (resource) => {
  selectedResource.value = resource
  grantTargetUsername.value = null
  grantDialogVisible.value = true
}

const grantAccess = async () => {
  if (!grantTargetUsername.value) {
    ElMessage.warning('请输入用户名')
    return
  }
  grantSaving.value = true
  try {
    const res = await dacOperation('grant', {
      resource_id: selectedResource.value.resource_id,
      target_username: grantTargetUsername.value
    })
    if (res.success) {
      ElMessage.success('授权成功')
      grantDialogVisible.value = false
      fetchAclList()
    } else {
      ElMessage.error(res.message || '授权失败')
    }
  } catch { ElMessage.error('授权失败') }
  finally { grantSaving.value = false }
}

const revokeAccess = async (acl) => {
  await ElMessageBox.confirm(
    `确认移除用户 #${acl.grantee_user_id} 对资源 #${selectedResource.value.resource_id} 的访问权？`,
    '提示',
    { type: 'warning' }
  )
  try {
    const res = await dacOperation('revoke', { acl_id: acl.acl_id })
    if (res.success) {
      ElMessage.success('已移除')
      fetchAclList()
    } else {
      ElMessage.error(res.message || '移除失败')
    }
  } catch { ElMessage.error('移除失败') }
}

const checkAccess = async () => {
  if (!checkResourceId.value) {
    ElMessage.warning('请输入资源ID')
    return
  }
  checkLoading.value = true
  try {
    const res = await checkDacAccess(checkResourceId.value)
    checkResult.value = res.data?.has_access ?? false
  } catch {
    checkResult.value = false
  }
  finally { checkLoading.value = false }
}

onMounted(fetchResources)
</script>

<style scoped>
.page-container {
  width: 100%;
}

.page-inner {
  max-width: 100%;
  margin: 0;
}

.dac-layout {
  display: flex;
  gap: 24px;
}

.dac-left {
  flex: 0 0 55%;
  min-width: 0;
}

.dac-right {
  flex: 1;
  flex-shrink: 0;
  min-width: 380px;
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

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #404040;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-wrapper {
  background: #fafafa;
  border-radius: 10px;
  padding: 2px 14px 4px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th {
  color: #8b8b8b;
  font-weight: 600;
  font-size: 14px;
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid #e5e5e5;
  vertical-align: middle;
}

td {
  color: #404040;
  font-size: 14px;
  padding: 10px 8px;
  vertical-align: middle;
}

.row-selected {
  background: rgba(59, 130, 246, 0.06);
}

.cell-mono {
  font-family: var(--font-family-mono);
  letter-spacing: 0.3px;
}

.action-btns {
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1;
}

.action-btn {
  height: 30px;
  padding: 0;
  font-size: 12px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #404040;
}

.action-btn:hover {
  background: #e5e5e5;
}

.action-btn-danger:hover {
  color: #dc2626;
  background: rgba(239, 68, 68, 0.08);
}

.btn-grant {
  height: 28px;
  padding: 0 12px;
  font-size: 12px;
  border-radius: 10px;
  background: #000;
  color: #fff;
  border: none;
}

.btn-grant:hover {
  background: #333;
}

.btn-grant-inline {
  height: 30px;
  padding: 0 14px;
  font-size: 12px;
  border-radius: 10px;
  background: #000;
  color: #fff;
  border: none;
}

.btn-grant-inline:hover {
  background: #333;
}

.btn-check {
  height: 32px;
  padding: 0 14px;
  font-size: 13px;
  border-radius: 10px;
  background: #000;
  color: #fff;
  border: none;
  margin-left: 8px;
}

.btn-check:hover {
  background: #333;
}

.check-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.check-result {
  font-size: 14px;
  font-weight: 500;
}

.has-access {
  color: #16a34a;
}

.no-access {
  color: #dc2626;
}

.empty-row {
  padding: 24px 8px;
  color: #8b8b8b;
  font-size: 13px;
}

.empty-center {
  text-align: center;
}
</style>
