import { ref } from 'vue'
import { io } from 'socket.io-client'
import axios from 'axios'
import { GW, currentUser, authHeaders } from './useAuth'

const WS_URL = import.meta.env.VITE_WS_URL

const users = ref([])
const usersOnline = ref({})
const messages = ref([])
const activeRecipient = ref(null)
let ws = null
let pollingTimer = null

// ───── USERS ─────
async function fetchUsers() {
  try {
    const { data } = await axios.get(`${GW}/chat/`, { headers: authHeaders() })
    users.value = (data.users_all || []).filter(u => u.id !== currentUser.value?.user_id)
    usersOnline.value = data.users_online || {}
  } catch {}
}

function startPolling() {
  stopPolling()
  pollingTimer = setInterval(fetchUsers, 50000)
}

function stopPolling() {
  if (pollingTimer) { clearInterval(pollingTimer); pollingTimer = null }
}

// ───── MESSAGES ─────
async function loadHistory(userId) {
  messages.value = []
  try {
    const { data } = await axios.get(`${GW}/chat/messages/${userId}`, { headers: authHeaders() })
    const list = Array.isArray(data) ? data : (data.data || [])
    messages.value = list
  } catch {}
}

async function sendMessage(text, fileUuids = { images: [], videos: [], audios: [] }) {
  if (!text && !fileUuids.images.length && !fileUuids.videos.length && !fileUuids.audios.length) return
  if (!activeRecipient.value) return
  await axios.post(`${GW}/chat/messages`, {
    recipient_id: activeRecipient.value.id,
    text: text || '',
    images: fileUuids.images,
    videos: fileUuids.videos,
    audios: fileUuids.audios,
  }, { headers: { ...authHeaders(), 'Content-Type': 'application/json' } })
}

async function openChat(user) {
  activeRecipient.value = user
  await loadHistory(user.id)
}

// ───── WEBSOCKET (native) ─────
// KrakenD не поддерживает WS — подключаемся напрямую к chat-service
function connectWS(onMessage) {
  if (!currentUser.value) return
  ws = new WebSocket(`${WS_URL}/ws/api/v1/real_time_chat/ws/${currentUser.value.user_id}`)

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    // Добавляем в messages если это текущий диалог
    if (
      activeRecipient.value &&
      (data.sender_id === activeRecipient.value.id || data.recipient_id === activeRecipient.value.id)
    ) {
      messages.value.push(data)
    }
    onMessage(data)
  }

  ws.onclose = () => setTimeout(() => connectWS(onMessage), 3000)

  return ws
}

function disconnectWS() {
  ws?.close()
  stopPolling()
}

// ───── SEARCH ─────
async function searchUsers(query) {
  if (!query.trim()) return []
  try {
    const { data } = await axios.get(`${GW}/user/search/`, { params: { search: query } })
    return (data.users || []).filter(u => u.id !== currentUser.value?.user_id)
  } catch { return [] }
}

export {
  users, usersOnline, messages, activeRecipient,
  fetchUsers, startPolling, stopPolling,
  loadHistory, sendMessage, openChat,
  connectWS, disconnectWS,
  searchUsers,
}
