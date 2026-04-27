import { ref } from 'vue'
import axios from 'axios'
import { beginRequest, endRequest, showToast } from './useToast'

const GW = import.meta.env.VITE_GW_URL

axios.defaults.withCredentials = true

function avatarUrl(uuid) {
  if (!uuid) return null
  return `${GW}/media_service/files/${uuid}/view/`
}

function getToken() { return localStorage.getItem('access_token') }
function setTokens(access, refresh) {
  if (access) localStorage.setItem('access_token', access)
  if (refresh) localStorage.setItem('refresh_token', refresh)
}
function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

axios.interceptors.request.use(config => {
  beginRequest()
  const token = getToken()
  if (token && !config.headers['Authorization']) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
}, err => {
  endRequest()
  return Promise.reject(err)
})

axios.interceptors.response.use(
  res => {
    endRequest()
    return res
  },
  err => {
    endRequest()
    if (err.response?.status === 429) {
      showToast('Слишко много запросов. Подождите немного...', 'warning')
      return Promise.reject(err)
    }

    // Network / CORS / no response
    if (!err.response) {
      showToast('Не удалось подключиться к серверу. Проверьте интернет или доступность VPS.', 'error')
      return Promise.reject(err)
    }

    // Do not spam for auth redirects/guards; components can handle it
    if (err.response.status === 401) return Promise.reject(err)

    const detail = err.response.data?.detail
    if (typeof detail === 'string' && detail.trim()) {
      showToast(detail, 'error')
      return Promise.reject(err)
    }

    if (err.response.status >= 500) {
      showToast('Ошибка сервера. Попробуйте позже.', 'error')
      return Promise.reject(err)
    }

    showToast('Ошибка запроса. Проверьте данные и попробуйте ещё раз.', 'error')
    return Promise.reject(err)
  }
)

const currentUser = ref(null)

async function fetchSelfInfo() {
  try {
    const { data } = await axios.get(`${GW}/user/self_info/`)
    currentUser.value = {
      user_id: data.user_db.id,
      username: data.user_db.username,
      role: data.user_db.role,
      is_active: data.user_db.is_active,
      avatarUrl: avatarUrl(data.user_db.avatar),
    }
    return true
  } catch { return false }
}

function updateAvatar(uuid) {
  if (currentUser.value) currentUser.value.avatarUrl = avatarUrl(uuid)
}

async function login(username, password) {
  const body = new FormData()
  body.append('username', username)
  body.append('password', password)
  const { data } = await axios.post(`${GW}/user/login/`, body)
  setTokens(data.access_token, data.refresh_token)
  await fetchSelfInfo()
}

async function register(username, password, avatarFile = null) {
  // 1. Регистрация без аватара
  const body = new FormData()
  body.append('username', username)
  body.append('password', password)
  await axios.post(`${GW}/user/register/`, body)

  // 2. Вход — получаем токены и user_id
  await login(username, password)

  // 3. Если есть файл — загружаем аватар с entity_id=user_id и обновляем профиль
  if (avatarFile && currentUser.value) {
    try {
      const { uploadAvatar, linkFile } = await import('./useMedia')
      const uuid = await uploadAvatar(avatarFile, currentUser.value.user_id)
      await linkFile(uuid)
      await updateUser({ avatar: uuid })
    } catch {
      // Аватар необязателен — продолжаем
    }
  }

  // 4. Устанавливаем флаг для показа онбординга
  localStorage.removeItem('rt_chat_onboarding_done')
}

async function updateUser(data) {
  const { data: updated } = await axios.patch(`${GW}/user/me/`, data)
  if (currentUser.value) {
    if (updated.username) currentUser.value.username = updated.username
    if (updated.avatar) currentUser.value.avatarUrl = avatarUrl(updated.avatar)
  }
  return updated
}

async function deleteUser() {
  await axios.delete(`${GW}/user/me/`)
  clearTokens()
  currentUser.value = null
}

async function logout() {
  try {
    await axios.post(`${GW}/user/logout/`, {})
  } finally {
    clearTokens()
    currentUser.value = null
  }
}

export { GW, avatarUrl, currentUser, getToken, fetchSelfInfo, updateAvatar, updateUser, deleteUser, login, register, logout }
