import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store'
import { checkSession } from '../api/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    redirect: '/dashboard',
    component: () => import('../views/Layout.vue'),
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'detection', name: 'Detection', component: () => import('../views/Detection.vue') },
      { path: 'reports', name: 'Reports', component: () => import('../views/Reports.vue') },
      { path: 'datasets', name: 'Datasets', component: () => import('../views/Datasets.vue') },
      { path: 'private-config', name: 'PrivateConfig', component: () => import('../views/PrivateConfig.vue') },
      { path: 'logs', name: 'Logs', component: () => import('../views/Logs.vue') },
      { path: 'dac', name: 'DacManager', component: () => import('../views/DacManager.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/Settings.vue') }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // 需要认证但本地无用户信息 → 跳转登录
  if (to.path !== '/login' && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  // 已认证但尚未通过服务端校验 → 调用 /api/auth/me 验证
  if (authStore.isAuthenticated && !authStore.sessionValidated) {
    try {
      const res = await checkSession()
      if (res && res.success) {
        // 服务端校验通过，更新本地用户信息
        authStore.setUser(res.data)
        // 校验通过后继续正常导航逻辑
      } else {
        authStore.logout()
        next('/login')
        return
      }
    } catch {
      // 401 或网络错误，拦截器已处理清除，保险起见也登出
      authStore.logout()
      next('/login')
      return
    }
  }

  // 已认证且已校验 → 正常放行
  if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
