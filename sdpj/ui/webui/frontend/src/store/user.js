import { defineStore } from 'pinia'
import { getProfile, getResources } from '../api/user'

export const useUserStore = defineStore('user', {
  state: () => ({
    profile: null,
    resources: []
  }),

  getters: {
    username: (state) => state.profile?.username || '',
    email: (state) => state.profile?.email || ''
  },

  actions: {
    async fetchProfile() {
      try {
        const res = await getProfile()
        if (res.success) {
          this.profile = res.profile
        }
        return res
      } catch (error) {
        console.error('获取用户资料失败', error)
        throw error
      }
    },

    async fetchResources() {
      try {
        const res = await getResources()
        if (res.success) {
          this.resources = res.resources
        }
        return res
      } catch (error) {
        console.error('获取用户资源失败', error)
        throw error
      }
    },

    clearProfile() {
      this.profile = null
      this.resources = []
    }
  }
})
