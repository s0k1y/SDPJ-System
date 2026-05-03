import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store'

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
      { path: 'settings', name: 'Settings', component: () => import('../views/Settings.vue') },
      { path: 'dac', name: 'DacManager', component: () => import('../views/DacManager.vue') },
      { path: 'datasets', name: 'Datasets', component: () => import('../views/Datasets.vue') },
      { path: 'private-config', name: 'PrivateConfig', component: () => import('../views/PrivateConfig.vue') }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.path !== '/login' && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
