<template>
  <div class="chat-area">
    <div class="chat-header">
      <template v-if="activeRecipient">
        <div class="avatar-circle">{{ activeRecipient.username[0].toUpperCase() }}</div>
        <span>{{ activeRecipient.username }}</span>
      </template>
      <span v-else class="no-chat">Выберите собеседника</span>
    </div>

    <div class="messages-box" ref="messagesBox">
      <div
        v-for="(m, i) in messages"
        :key="m.id || i"
        :class="['message', isOwn(m) ? 'outgoing' : 'incoming']"
      >
        {{ m.text }}
        <div class="meta">{{ formatTime(m.created_at) }}</div>
      </div>
    </div>

    <div class="chat-input-area">
      <input
        v-model="inputText"
        placeholder="Сообщение..."
        :disabled="!activeRecipient"
        @keydown.enter="send"
      />
      <button class="btn btn-primary" @click="send">→</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  messages: Array,
  activeRecipient: Object,
  currentUser: Object,
})
const emit = defineEmits(['send'])

const inputText = ref('')
const messagesBox = ref(null)

watch(() => props.messages.length, async () => {
  await nextTick()
  if (messagesBox.value) messagesBox.value.scrollTop = messagesBox.value.scrollHeight
})

function isOwn(m) {
  return m.sender_id === props.currentUser?.user_id
}

function formatTime(ts) {
  return ts ? new Date(ts).toLocaleTimeString() : new Date().toLocaleTimeString()
}

function send() {
  const text = inputText.value.trim()
  if (!text || !props.activeRecipient) return
  emit('send', text)
  inputText.value = ''
}
</script>

<style scoped>
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 14px 20px;
  border-bottom: 1px solid #2a2d3a;
  font-size: 14px;
  font-weight: 600;
  color: #ccc;
  display: flex;
  align-items: center;
  gap: 10px;
}

.no-chat { color: #555; font-weight: 400; font-size: 13px; }

.avatar-circle {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: #7c6af7;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; color: #fff;
  flex-shrink: 0;
}

.messages-box {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message {
  max-width: 65%;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  word-break: break-word;
}

.message.incoming {
  background: #2a2d3a;
  color: #ddd;
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}

.message.outgoing {
  background: #7c6af7;
  color: #fff;
  align-self: flex-end;
  border-bottom-right-radius: 4px;
}

.meta {
  font-size: 10px;
  opacity: .6;
  margin-top: 4px;
  text-align: right;
}

.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid #2a2d3a;
  display: flex;
  gap: 8px;
}

.chat-input-area input {
  flex: 1;
  background: #0f1117;
  border: 1px solid #2a2d3a;
  border-radius: 8px;
  padding: 10px 14px;
  color: #e0e0e0;
  font-size: 13px;
  outline: none;
  transition: border-color .2s;
}
.chat-input-area input:focus { border-color: #7c6af7; }
.chat-input-area input:disabled { opacity: .4; }

.btn {
  padding: 10px 18px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: opacity .2s;
}
.btn:hover { opacity: .85; }
.btn-primary { background: #7c6af7; color: #fff; }
</style>
