<template>
  <div class="chat-screen">
    <Sidebar
      :users="users"
      :users-online="usersOnline"
      :active-recipient="activeRecipient"
      :ws-connected="wsConnected"
      :me-name="currentUser?.username"
      @open-chat="handleOpenChat"
      @logout="handleLogout"
    />
    <ChatArea
      :messages="messages"
      :active-recipient="activeRecipient"
      :current-user="currentUser"
      @send="handleSend"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from './Sidebar.vue'
import ChatArea from './ChatArea.vue'
import { currentUser, logout } from '../useAuth'
import {
  users, usersOnline, messages, activeRecipient,
  fetchUsers, startPolling, stopPolling,
  openChat, sendMessage, connectWS, disconnectWS,
} from '../useChat'

const emit = defineEmits(['logout'])
const wsConnected = ref(false)
let ws = null

onMounted(async () => {
  await fetchUsers()
  startPolling()
  ws = connectWS(onIncomingMessage)
  ws.onopen = () => wsConnected.value = true
  ws.onclose = () => {
    wsConnected.value = false
    // reconnect уже внутри connectWS
  }
})

onUnmounted(() => {
  disconnectWS()
})

function onIncomingMessage(data) {
  // Автопереход если пишет не текущий собеседник
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

async function handleSend(text) {
  await sendMessage(text)
}

async function handleLogout() {
  disconnectWS()
  try {
    await logout()
  } finally {
    emit('logout')
  }
}
</script>

<style scoped>
.chat-screen {
  width: 900px;
  height: 580px;
  background: #1c1f2e;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(0,0,0,.5);
  display: flex;
}
</style>
