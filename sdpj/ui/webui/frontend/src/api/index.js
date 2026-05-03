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
      clearAll()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
