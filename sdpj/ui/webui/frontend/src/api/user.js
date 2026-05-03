import api from './index'

/**
 * 账户操作（修改密码、更新信息等）
 */
export function accountOperation(operation, params = {}) {
  return api.post('/users/account', { operation, params })
}

/**
 * 获取用户资料
 */
export function getProfile() {
  return api.get('/users/profile')
}

/**
 * 获取用户资源列表
 */
export function getResources() {
  return api.get('/users/resources')
}

/**
 * DAC 权限操作
 */
export function dacOperation(operation, params = {}) {
  return api.post('/users/dac', { operation, params })
}

/**
 * 检查资源访问权限
 */
export function checkDacAccess(resourceId) {
  return api.get('/users/dac/check', { params: { resource_id: resourceId } })
}
