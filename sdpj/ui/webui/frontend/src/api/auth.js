import api from './index'

export async function login(username, password) {
  return api.post('/auth/login', { username, password })
}

export async function register(username, password) {
  return api.post('/auth/register', { username, password })
}

export async function logout() {
  return api.post('/auth/logout')
}
