import api from './index'

/**
 * 生成报告
 */
export function generateReport(taskGroupId, detectionType) {
  return api.post('/reports/generate', {
    task_group_id: taskGroupId,
    detection_type: detectionType
  })
}

/**
 * 获取报告列表
 */
export function getReportList(params = {}) {
  return api.get('/reports/list', { params })
}

/**
 * 获取单个报告详情
 */
export function getReport(taskGroupId) {
  return api.get(`/reports/${taskGroupId}`)
}

/**
 * 删除报告
 */
export function deleteReport(targetId, granularity = 'report') {
  return api.delete(`/reports/${targetId}`, { params: { granularity } })
}

/**
 * 导出报告
 */
export function exportReport(taskGroupId, targetFormat = 'jsonl') {
  return api.post('/reports/export', {
    task_group_id: taskGroupId,
    target_format: targetFormat
  })
}

/**
 * 获取报告可视化数据
 */
export function getVisualization(taskGroupId) {
  return api.get(`/reports/${taskGroupId}/visualization`)
}

export function getComplianceStatistics() {
  return api.get('/reports/statistics')
}
