import { defineStore } from 'pinia'
import { getUser, setUser as saveUser, clearAll } from '../utils/storage'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isAuthenticated: !!getUser(),
    user: getUser(),
    sessionValidated: false  // 标记当前会话是否已通过服务端校验
  }),
  actions: {
    setUser(user) {
      this.user = user
      this.isAuthenticated = true
      this.sessionValidated = true
      saveUser(user)
    },
    logout() {
      this.isAuthenticated = false
      this.user = null
      this.sessionValidated = false
      clearAll()
    },
    markSessionValidated() {
      this.sessionValidated = true
    }
  }
})

export const useDetectionStore = defineStore('detection', {
  state: () => ({
    tasks: [],
    currentTask: null
  }),
  actions: {
    addTask(task) {
      this.tasks.push(task)
    },
    setCurrentTask(task) {
      this.currentTask = task
    }
  }
})
