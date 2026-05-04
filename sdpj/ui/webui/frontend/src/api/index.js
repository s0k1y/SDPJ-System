import axios from 'axios'
import { clearAll } from '../utils/storage'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  withCredentials: true,
})

api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // 只在非登录页面时才清除存储并重定向
      if (window.location.pathname !== '/login') {
        clearAll()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
