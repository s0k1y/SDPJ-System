<template>
  <div class="page-container">
    <div class="page-inner">
      <h1 class="page-title">系统设置</h1>
      <p class="page-info">管理个人信息和修改密码</p>

      <div class="form-section" v-loading="profileLoading">
        <el-form :model="profileForm" label-width="120px">
          <el-form-item label="用户名">
            <el-input v-model="profileForm.username" disabled />
          </el-form-item>
        </el-form>
      </div>

      <div class="form-divider"></div>

      <div class="form-section">
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
            <el-button class="btn-save" @click="changePassword" :loading="changingPwd">修改密码</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getProfile, accountOperation } from '../api/user'
import { encryptPassword } from '../utils/crypto'

const profileLoading = ref(false)
const changingPwd = ref(false)
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

const fetchProfile = async () => {
  profileLoading.value = true
  try {
    const res = await getProfile()
    if (res.success && res.profile) {
      profileForm.value.username = res.profile.username || ''
    }
  } catch { /* 使用默认值 */ }
  finally { profileLoading.value = false }
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
  } catch { ElMessage.error('密码修改失败') }
  finally { changingPwd.value = false }
}

onMounted(fetchProfile)
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

.form-section {
  max-width: 480px;
}

.form-divider {
  height: 1px;
  background: #e5e5e5;
  margin: 32px 0;
  max-width: 480px;
}

.btn-save {
  height: 34px;
  padding: 0 14px;
  font-size: 14px;
  border-radius: 10px;
  background: #000;
  color: #fff;
  border: none;
}

.btn-save:hover {
  background: #333;
}
</style>
