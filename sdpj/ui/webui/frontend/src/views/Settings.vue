<template>
  <PageLayout title="系统设置" description="管理个人信息、密码和检测配置">
    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="个人信息" name="profile">
          <el-form :model="profileForm" label-width="120px" v-loading="profileLoading">
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveProfile" :loading="saving">保存</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="修改密码" name="password">
          <el-form :model="passwordForm" :rules="passwordRules" ref="pwdFormRef" label-width="120px">
            <el-form-item label="原密码" prop="oldPassword">
              <el-input v-model="passwordForm.oldPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="changingPwd">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="检测配置" name="detection">
          <el-form :model="detectionConfig" label-width="120px">
            <el-form-item label="默认并发数">
              <el-input-number v-model="detectionConfig.concurrency" :min="1" :max="10" />
            </el-form-item>
            <el-form-item label="超时时间(秒)">
              <el-input-number v-model="detectionConfig.timeout" :min="30" :max="3600" :step="30" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveDetectionConfig" :loading="savingConfig">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getProfile, accountOperation } from '../api/user'
import { encryptPassword } from '../utils/crypto'
import { detectionConfig as detectionConfigApi } from '../api/detection'
import PageLayout from '../components/common/PageLayout.vue'

const activeTab = ref('profile')
const profileLoading = ref(false)
const saving = ref(false)
const changingPwd = ref(false)
const savingConfig = ref(false)
const pwdFormRef = ref()

const profileForm = ref({ username: '' })

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度为 6-32 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordForm.value.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const detectionConfig = ref({ concurrency: 1, timeout: 300 })

const fetchProfile = async () => {
  profileLoading.value = true
  try {
    const res = await getProfile()
    if (res.success && res.profile) {
      profileForm.value.username = res.profile.username || ''
    }
  } catch {
    // 使用默认值
  } finally {
    profileLoading.value = false
  }
}

const saveProfile = async () => {
  saving.value = true
  try {
    const res = await accountOperation('update_profile', { username: profileForm.value.username })
    if (res.success) ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const changePassword = async () => {
  await pwdFormRef.value.validate()
  changingPwd.value = true
  try {
    const encOld = await encryptPassword(passwordForm.value.oldPassword)
    const encNew = await encryptPassword(passwordForm.value.newPassword)
    const res = await accountOperation('change_password', {
      old_password: encOld,
      new_password: encNew,
      is_encrypted: true
    })
    if (res.success) {
      ElMessage.success('密码修改成功')
      passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
    }
  } catch {
    ElMessage.error('密码修改失败')
  } finally {
    changingPwd.value = false
  }
}

const saveDetectionConfig = async () => {
  savingConfig.value = true
  try {
    const res = await detectionConfigApi('update', {
      concurrency: detectionConfig.value.concurrency,
      timeout: detectionConfig.value.timeout
    })
    if (res.success) ElMessage.success('配置保存成功')
  } catch {
    ElMessage.error('配置保存失败')
  } finally {
    savingConfig.value = false
  }
}

onMounted(fetchProfile)
</script>

<style scoped>
/* 无需额外样式，由 PageLayout 统一管理 */
</style>
