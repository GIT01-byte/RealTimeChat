<template>
  <div class="chat-screen">
    <Sidebar
      v-show="!isMobile || !activeRecipient"
      :users="users"
      :users-online="usersOnline"
      :active-recipient="activeRecipient"
      :loading-users="loadingUsers"
      :ws-connected="wsConnected"
      :me-name="currentUser?.username"
      @open-chat="handleOpenChat"
      @logout="handleLogout"
    />
    <ChatArea
      v-show="!isMobile || activeRecipient"
      :messages="messages"
      :active-recipient="activeRecipient"
      :current-user="currentUser"
      :is-mobile="isMobile"
      :loading-history="loadingHistory"
      @send="handleSend"
      @back="activeRecipient = null"
    />

    <OnboardingGuide v-if="showOnboarding" @done="finishOnboarding" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from './Sidebar.vue'
import ChatArea from './ChatArea.vue'
import OnboardingGuide from './OnboardingGuide.vue'
import { currentUser, logout } from '../useAuth'
import { showToast } from '../useToast'
import {
  users, usersOnline, messages, activeRecipient, loadingUsers, loadingHistory,
  fetchUsers, startPolling, stopPolling,
  openChat, sendMessage, connectWS, disconnectWS,
} from '../useChat'

const ONBOARDING_KEY = 'rt_chat_onboarding_done'

const router = useRouter()
const wsConnected = ref(false)
const isMobile = ref(window.innerWidth <= 900 && window.innerHeight > window.innerWidth)
const showOnboarding = ref(false)
let ws = null
let wsEverOpened = false
let wsWarned = false

function warnWsUnavailableOnce() {
  if (wsWarned) return
  wsWarned = true
  showToast(
    'WebSocket недоступен — сообщения обновляются не мгновенно. Переключайтесь между пользователями, чтобы обновить историю. Мы уже чиним.',
    'warning',
    9000
  )
}

function onResize() {
  isMobile.value = window.innerWidth <= 900 && window.innerHeight > window.innerWidth
}

function finishOnboarding() {
  showOnboarding.value = false
  localStorage.setItem(ONBOARDING_KEY, '1')
}

onMounted(async () => {
  window.addEventListener('resize', onResize)
  await fetchUsers()
  startPolling()
  ws = connectWS(onIncomingMessage)
  ws.onopen = () => {
    wsEverOpened = true
    wsConnected.value = true
  }
  ws.onerror = () => {
    // Если даже не смогли установить соединение — покажем предупреждение один раз.
    if (!wsEverOpened) warnWsUnavailableOnce()
  }
  ws.onclose = () => {
    wsConnected.value = false
    // close до onopen (или сразу после попытки) — тоже считаем "неудачным подключением".
    if (!wsEverOpened) warnWsUnavailableOnce()
  }

  if (!localStorage.getItem(ONBOARDING_KEY)) {
    showOnboarding.value = true
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  disconnectWS()
})

function onIncomingMessage(data) {
  if (
    data.sender_id !== currentUser.value?.user_id &&
    (!activeRecipient.value || activeRecipient.value.id !== data.sender_id)
  ) {
    const sender = users.value.find(u => u.id === data.sender_id)
    if (sender) handleOpenChat(sender)
  }
}

async function handleOpenChat(user) {
  await openChat(user)
}

async function handleSend({ text, fileUuids }) {
  await sendMessage(text, fileUuids)
}

async function handleLogout() {
  disconnectWS()
  try { await logout() } finally { router.push('/') }
}
</script>

<style scoped>
.chat-screen {
  width: min(900px, 100vw);
  height: min(580px, 100dvh);
  background: #1c1f2e;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(0,0,0,.5), 0 0 0 1px rgba(124,106,247,.08);
  display: flex;
}

@media (max-width: 900px) {
  .chat-screen {
    border-radius: 0;
    box-shadow: none;
    width: 100vw;
    height: 100dvh;
  }
}

@media (max-width: 900px) and (orientation: landscape) {
  .chat-screen {
    height: 100dvh;
    padding-left: env(safe-area-inset-left);
    padding-right: env(safe-area-inset-right);
  }
}
</style>
