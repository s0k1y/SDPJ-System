import api from './index'

/**
 * 获取日志列表
 * @param {Object} params - 查询参数
 * @param {string} params.category - 日志类别 (app/error/access/audit)
 * @param {string} params.source_module - 来源模块
 * @param {string} params.user_id - 用户ID
 * @param {string} params.start_time - 开始时间
 * @param {string} params.end_time - 结束时间
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 */
export function getLogList(params = {}) {
  return api.get('/logs', { params })
}
