<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>SDPJ-System</h2>
      <p class="subtitle">大模型安全检测平台</p>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form :model="form" :rules="rules" ref="loginFormRef">
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="用户名" size="large">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="密码" size="large">
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-button type="primary" size="large" style="width:100%" @click="handleLogin" :loading="loading">
              登录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="regForm" :rules="regRules" ref="regFormRef">
            <el-form-item prop="username">
              <el-input v-model="regForm.username" placeholder="用户名" size="large">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="regForm.password" type="password" placeholder="密码" size="large">
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-button type="primary" size="large" style="width:100%" @click="handleRegister" :loading="loading">
              注册
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { login, register } from '../api/auth'
import { useAuthStore } from '../store'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const activeTab = ref('login')
const loginFormRef = ref()
const regFormRef = ref()

const form = ref({ username: '', password: '' })
const regForm = ref({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
const regRules = rules

const handleLogin = async () => {
  await loginFormRef.value.validate()
  loading.value = true
  try {
    const res = await login(form.value.username, form.value.password)
    if (res.success) {
      authStore.setLoggedIn(res.user_id)
      ElMessage.success('登录成功')
      router.push('/')
    }
  } catch {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  await regFormRef.value.validate()
  loading.value = true
  try {
    const res = await register(regForm.value.username, regForm.value.password)
    if (res.success) {
      ElMessage.success('注册成功，请登录')
      activeTab.value = 'login'
    } else {
      ElMessage.error(res.message || '注册失败')
    }
  } catch {
    ElMessage.error('注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card { width: 400px; padding: 20px; }
h2 { text-align: center; margin-bottom: 10px; color: #303133; }
.subtitle { text-align: center; color: #909399; margin-bottom: 20px; }
</style>
