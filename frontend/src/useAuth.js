import { ref } from 'vue'
import axios from 'axios'
import { showToast } from './useToast'

const GW = import.meta.env.VITE_GW_URL

// ───── Axios interceptor — перехватывает 429 везде ─────
axios.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 429) {
      showToast('Слишко много запросов. Подождите немного...', 'warning')
    }
    return Promise.reject(err)
  }
)

const currentUser = ref(null)

function getToken() { return localStorage.getItem('access_token') }
function getRefreshToken() { return localStorage.getItem('refresh_token') }
function setTokens(access, refresh) {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}
function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

function authHeaders() {
  return { Authorization: `Bearer ${getToken()}` }
}

async function fetchSelfInfo() {
  try {
    const { data } = await axios.get(`${GW}/user/self_info/`, { headers: authHeaders() })
    currentUser.value = {
      user_id: data.user_db.id,
      username: data.user_db.username,
      role: data.user_db.role,
      is_active: data.user_db.is_active,
    }
    return true
  } catch { return false }
}

async function login(username, password) {
  const body = new FormData()
  body.append('username', username)
  body.append('password', password)
  const { data } = await axios.post(`${GW}/user/login/`, body)
  setTokens(data.access_token, data.refresh_token)
  await fetchSelfInfo()
}

async function register(username, password) {
  const body = new FormData()
  body.append('username', username)
  body.append('password', password)
  await axios.post(`${GW}/user/register/`, body)
  await login(username, password)
}

async function logout() {
  try {
    await axios.post(`${GW}/user/logout/`, {}, { headers: authHeaders() })
  } finally {
    clearTokens()
    currentUser.value = null
  }
}

export { GW, currentUser, getToken, authHeaders, fetchSelfInfo, login, register, logout }
