<template>
  <div class="login-container">
    <!-- 桌面端左侧品牌展示区 -->
    <div class="brand-section">
      <div class="brand-content">
        <h1 class="brand-title">SDPJ-System</h1>
        <p class="brand-subtitle">大语言模型安全风险检测和防御系统-检测系统设计（论文替代）</p>
        <div class="brand-features">
          <div class="feature-item">
            <span class="feature-label">Keywords:</span>
          </div>
          <div class="feature-item feature-item--indent">
            <span>Artificial Intelligence</span>
          </div>
          <div class="feature-item feature-item--indent">
            <span>Security Risk Detection</span>
          </div>
          <div class="feature-item feature-item--indent">
            <span>Self–Detection based on Post–Jialbreak Algorithm</span>
          </div>
          <div class="feature-item">
            <span class="feature-label">攻击检测:</span> 提示词注入
          </div>
          <div class="feature-item">
            <span class="feature-label">攻击路径分类:</span> 直接，间接(多模态、多编码)
          </div>
          <div class="feature-item">
            <span class="feature-label">攻击意图分类:</span> 越狱、劫持、泄露
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单区 -->
    <div class="form-section">
      <div class="login-card">
        <div class="card-header">
          <h2 class="card-title">{{ activeTab === 'login' ? '登录' : '注册' }}</h2>
          <p class="card-description">{{ activeTab === 'login' ? '使用您的账户登录系统' : '创建新账户以开始使用' }}</p>
        </div>

        <el-tabs v-model="activeTab" class="auth-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form :model="form" :rules="rules" ref="loginFormRef" @keyup.enter="handleLogin">
              <el-form-item prop="username">
                <el-input v-model="form.username" placeholder="用户名" size="large">
                  <template #prefix><el-icon><User /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password>
                  <template #prefix><el-icon><Lock /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-button type="primary" size="large" class="submit-button" @click="handleLogin" :loading="loading">
                登录
              </el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form :model="regForm" :rules="regRules" ref="regFormRef" @keyup.enter="handleRegister">
              <el-form-item prop="username">
                <el-input v-model="regForm.username" placeholder="用户名" size="large">
                  <template #prefix><el-icon><User /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="regForm.password" type="password" placeholder="密码" size="large" show-password>
                  <template #prefix><el-icon><Lock /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-button type="primary" size="large" class="submit-button" @click="handleRegister" :loading="loading">
                注册
              </el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { login, register } from '../api/auth'
import { useAuthStore } from '../store'
import api from '../api'

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
  try {
    await loginFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const res = await login(form.value.username, form.value.password)
    console.log('登录响应:', res)

    if (res && res.success) {
      // 直接保存用户名（使用登录时输入的用户名）
      authStore.setUser({
        user_id: res.user_id,
        username: form.value.username
      })

      ElMessage.success('登录成功')
      await new Promise(resolve => setTimeout(resolve, 100))
      await router.push('/dashboard')
    } else {
      ElMessage.error(res?.message || '登录失败')
    }
  } catch (error) {
    console.error('登录错误:', error)
    // 显示具体的错误信息
    const errorMsg = error.response?.data?.detail || error.message || '登录失败，请检查用户名和密码'
    ElMessage.error(errorMsg)
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
  min-height: 100vh;
  background: var(--color-bg);
  /* 几何纹理背景 */
  background-image: radial-gradient(circle at 1px 1px, var(--color-gray-200) 1px, transparent 0);
  background-size: 40px 40px;
}

/* 左侧品牌展示区 */
.brand-section {
  display: none;
  flex: 1;
  background: var(--color-primary-darker);
  color: white;
  padding: var(--spacing-16);
  align-items: center;
  justify-content: center;
}

.brand-content {
  max-width: 700px;
}

.brand-title {
  font-size: 3.5rem;
  font-weight: var(--font-weight-extrabold);
  color: white;
  letter-spacing: -0.02em;
  margin-bottom: var(--spacing-2);
}

.brand-title-en {
  font-size: 1rem;
  font-weight: var(--font-weight-medium);
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.05em;
  margin-bottom: var(--spacing-10);
}

.brand-subtitle {
  font-size: var(--font-size-xl);
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: var(--spacing-16);
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  font-size: var(--font-size-base);
  color: rgba(255, 255, 255, 0.75);
}

.feature-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.2);
  font-size: var(--font-size-sm);
}

.feature-item--indent {
  padding-left: var(--spacing-8);
  font-size: var(--font-size-base);
  color: rgba(255, 255, 255, 0.75);
}

.feature-label {
  color: rgba(255, 255, 255, 0.95);
  font-weight: var(--font-weight-medium);
}

/* 右侧表单区 */
.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
}

.login-card {
  width: clamp(360px, 90vw, 440px);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-gray-300);
  padding: var(--spacing-12);
}

.card-header {
  margin-bottom: var(--spacing-8);
}

.card-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--spacing-2);
}

.card-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.auth-tabs {
  margin-top: var(--spacing-6);
}

/* 提交按钮 */
.submit-button {
  width: 100%;
}

/* 定制 Tab 样式 */
.auth-tabs :deep(.el-tabs__header) {
  margin-bottom: var(--spacing-6);
}

.auth-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: var(--color-gray-400);
}

.auth-tabs :deep(.el-tabs__item) {
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
  padding: 0 var(--spacing-5);
  height: 44px;
  line-height: 44px;
}

.auth-tabs :deep(.el-tabs__item:hover) {
  color: var(--color-text);
}

.auth-tabs :deep(.el-tabs__item.is-active) {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.auth-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--color-primary);
  height: 3px;
}

/* 桌面端显示左侧品牌区 */
@media (min-width: 1024px) {
  .brand-section {
    display: flex;
  }
}
</style>
