import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token
  },
  
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem('token', token)
    },
    
    clearToken() {
      this.token = ''
      localStorage.removeItem('token')
    },
    
    setUser(user) {
      this.user = user
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
