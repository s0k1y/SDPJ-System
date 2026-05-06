import api from './index'

/**
 * 启动检测任务
 */
export function startDetection(data) {
  return api.post('/detection/start', data)
}

/**
 * 运行检测队列
 */
export function runDetection(maxConcurrency = 1) {
  return api.post('/detection/run', { max_concurrency: maxConcurrency })
}

/**
 * 获取所有任务进度
 */
export function getProgress() {
  return api.get('/detection/progress')
}

/**
 * 获取单个任务进度
 */
export function getTaskProgress(taskId) {
  return api.get(`/detection/progress/${taskId}`)
}

/**
 * 获取数据集列表
 */
export function getDatasets() {
  return api.get('/detection/datasets')
}

/**
 * 检测配置操作
 */
export function cancelTask(params) {
  return api.post('/detection/cancel', params)
}

export function detectionConfig(operation, params = {}) {
  return api.post('/detection/config', { operation, params })
}

/**
 * 检测资源操作
 */
export function detectionResource(operation, params = {}) {
  return api.post('/detection/resource', { operation, params })
}
