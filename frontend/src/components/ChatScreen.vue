<template>
  <div class="chat-screen">
    <!-- На мобиле показываем либо сайдбар либо чат -->
    <Sidebar
      v-show="!isMobile || !activeRecipient"
      :users="users"
      :users-online="usersOnline"
      :active-recipient="activeRecipient"
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
      @send="handleSend"
      @back="activeRecipient = null"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from './Sidebar.vue'
import ChatArea from './ChatArea.vue'
import { currentUser, logout } from '../useAuth'
import {
  users, usersOnline, messages, activeRecipient,
  fetchUsers, startPolling, stopPolling,
  openChat, sendMessage, connectWS, disconnectWS,
} from '../useChat'

const router = useRouter()
const wsConnected = ref(false)
const isMobile = ref(window.innerWidth <= 900)
let ws = null

function onResize() {
  isMobile.value = window.innerWidth <= 900
}

onMounted(async () => {
  window.addEventListener('resize', onResize)
  await fetchUsers()
  startPolling()
  ws = connectWS(onIncomingMessage)
  ws.onopen = () => wsConnected.value = true
  ws.onclose = () => { wsConnected.value = false }
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
  box-shadow: 0 8px 40px rgba(0,0,0,.5);
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
</style>
