/**
 * HTTP 请求工具 - 重新导出 api/index.js 中的 axios 实例
 */
import api from '../api'

export default api

export const get = (url, params) => api.get(url, { params })
export const post = (url, data) => api.post(url, data)
export const put = (url, data) => api.put(url, data)
export const del = (url, params) => api.delete(url, { params })
