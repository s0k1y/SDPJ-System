import { defineStore } from 'pinia'
import { getUser, setUser as saveUser, clearAll } from '../utils/storage'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isAuthenticated: false,
    user: getUser()
  }),
  actions: {
    setLoggedIn(userId) {
      this.isAuthenticated = true
    },
    setUser(user) {
      this.user = user
      saveUser(user)
    },
    logout() {
      this.isAuthenticated = false
      this.user = null
      clearAll()
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
