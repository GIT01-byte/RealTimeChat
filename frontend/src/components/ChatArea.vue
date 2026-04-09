<template>
  <div class="chat-area">
    <div class="chat-header">
      <button v-if="isMobile && activeRecipient" class="back-btn" @click="$emit('back')">←</button>
      <template v-if="activeRecipient">
        <div class="avatar-circle">{{ activeRecipient.username[0].toUpperCase() }}</div>
        <span>{{ activeRecipient.username }}</span>
      </template>
      <span v-else class="no-chat">Выберите собеседника</span>
    </div>

    <div class="messages-box" ref="messagesBox">
      <div v-if="!activeRecipient" class="empty-chat">
        <div class="empty-icon">💬</div>
        <div class="empty-text">Выберите кому хотели бы отправить сообщение</div>
      </div>
      <div
        v-for="(m, i) in messages"
        :key="m.id || i"
        :class="['message', isOwn(m) ? 'outgoing' : 'incoming']"
      >
        <div v-if="m.text" class="msg-text">{{ m.text }}</div>

        <!-- Медиафайлы -->
        <MessageMedia
          v-if="hasFiles(m)"
          :images="m.images || []"
          :videos="m.videos || []"
          :audios="m.audios || []"
        />

        <div class="meta">{{ formatTime(m.created_at) }}</div>
      </div>
    </div>

    <!-- Прикреплённые файлы (превью) -->
    <div v-if="attachments.length" class="attachments-preview">
      <div v-for="(a, i) in attachments" :key="i" class="attachment-item">
        <span class="attachment-icon">{{ fileIcon(a.type) }}</span>
        <span class="attachment-name">{{ a.file.name }}</span>
        <span class="attachment-remove" @click="removeAttachment(i)">✕</span>
      </div>
    </div>

    <div class="chat-input-area">
      <!-- Кнопка скрепки -->
      <div class="attach-btn" @click="toggleAttachMenu" :class="{ active: showAttachMenu }">
        📎
      </div>

      <!-- Меню прикрепления -->
      <div v-if="showAttachMenu" class="attach-menu">
        <label class="attach-option">
          🖼️ Фото
          <input type="file" accept="image/*" multiple @change="onFileSelect($event, 'image')" hidden />
        </label>
        <label class="attach-option">
          🎬 Видео
          <input type="file" accept="video/*" multiple @change="onFileSelect($event, 'video')" hidden />
        </label>
        <label class="attach-option">
          🎵 Аудио
          <input type="file" accept="audio/*" multiple @change="onFileSelect($event, 'audio')" hidden />
        </label>
      </div>

      <input
        v-model="inputText"
        placeholder="Сообщение..."
        :disabled="!activeRecipient"
        @keydown.enter="send"
        @click="showAttachMenu = false"
      />
      <button
        class="btn btn-primary"
        :disabled="sending || (!inputText.trim() && !attachments.length)"
        @click="send"
      >
        {{ sending ? '...' : '→' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { showToast } from '../useToast'
import { uploadFiles, linkFile } from '../useMedia'
import MessageMedia from './MessageMedia.vue'

const props = defineProps({
  messages: Array,
  activeRecipient: Object,
  currentUser: Object,
  isMobile: { type: Boolean, default: false },
})
const emit = defineEmits(['send', 'back'])

const inputText = ref('')
const messagesBox = ref(null)
const attachments = ref([])   // [{ file, type: 'image'|'video'|'audio' }]
const showAttachMenu = ref(false)
const sending = ref(false)

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

function hasFiles(m) {
  return (m.images?.length || m.videos?.length || m.audios?.length)
}

function fileIcon(type) {
  return { image: '🖼️', video: '🎬', audio: '🎵' }[type] || '📎'
}

function toggleAttachMenu() {
  showAttachMenu.value = !showAttachMenu.value
}

function onFileSelect(e, type) {
  const files = Array.from(e.target.files)
  files.forEach(file => attachments.value.push({ file, type }))
  showAttachMenu.value = false
  e.target.value = ''
}

function removeAttachment(i) {
  attachments.value.splice(i, 1)
}

async function send() {
  const text = inputText.value.trim()
  if ((!text && !attachments.value.length) || !props.activeRecipient || sending.value) return

  sending.value = true
  try {
    const fileUuids = { images: [], videos: [], audios: [] }

    // 1. Загружаем файлы по типам
    if (attachments.value.length) {
      const imageFiles = attachments.value.filter(a => a.type === 'image').map(a => a.file)
      const videoFiles = attachments.value.filter(a => a.type === 'video').map(a => a.file)
      const audioFiles = attachments.value.filter(a => a.type === 'audio').map(a => a.file)

      if (imageFiles.length) fileUuids.images = await uploadFiles(imageFiles)
      if (videoFiles.length) fileUuids.videos = await uploadFiles(videoFiles)
      if (audioFiles.length) fileUuids.audios = await uploadFiles(audioFiles)
    }

    // 2. Отправляем сообщение
    emit('send', { text, fileUuids })
    inputText.value = ''
    attachments.value = []

    // 3. Привязываем файлы к сообщению
    const allUuids = [...fileUuids.images, ...fileUuids.videos, ...fileUuids.audios]
    await Promise.allSettled(allUuids.map(uuid => linkFile(uuid)))

  } catch (e) {
    showToast('Ошибка при отправке сообщения', 'error')
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.chat-area { flex: 1; display: flex; flex-direction: column; position: relative; }

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

.back-btn {
  background: none;
  border: none;
  color: #7c6af7;
  font-size: 20px;
  cursor: pointer;
  padding: 0 8px 0 0;
  line-height: 1;
}

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

.msg-text { margin-bottom: 4px; }

.meta { font-size: 10px; opacity: .6; margin-top: 4px; text-align: right; }

.empty-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #555;
}

.empty-icon { font-size: 48px; }
.empty-text { font-size: 14px; }

/* Attachments preview */
.attachments-preview {
  padding: 8px 16px;
  border-top: 1px solid #2a2d3a;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #2a2d3a;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
  color: #ccc;
}

.attachment-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-remove {
  cursor: pointer;
  color: #888;
  font-size: 11px;
  margin-left: 2px;
}
.attachment-remove:hover { color: #e74c3c; }

/* Input area */
.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid #2a2d3a;
  display: flex;
  gap: 8px;
  align-items: center;
  position: relative;
}

.attach-btn {
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: background .15s;
  user-select: none;
}
.attach-btn:hover, .attach-btn.active { background: #2a2d3a; }

.attach-menu {
  position: absolute;
  bottom: 56px;
  left: 12px;
  background: #1c1f2e;
  border: 1px solid #2a2d3a;
  border-radius: 10px;
  overflow: hidden;
  z-index: 20;
  box-shadow: 0 4px 16px rgba(0,0,0,.4);
}

.attach-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  font-size: 13px;
  color: #ccc;
  cursor: pointer;
  transition: background .15s;
}
.attach-option:hover { background: #2a2d3a; }

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
.btn:disabled { opacity: .4; cursor: not-allowed; }
.btn-primary { background: #7c6af7; color: #fff; }
</style>
