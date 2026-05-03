import api from './index'
import { encryptPassword } from '../utils/crypto'

export async function login(username, password) {
  const enc = await encryptPassword(password)
  return api.post('/auth/login', { username, password: enc })
}

export async function register(username, password) {
  const enc = await encryptPassword(password)
  return api.post('/auth/register', { username, password: enc })
}

export async function logout() {
  return api.post('/auth/logout')
}
