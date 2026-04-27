<template>
  <div class="chat-area">
    <div class="chat-header">
      <button v-if="isMobile && activeRecipient" class="back-btn" @click="$emit('back')">←</button>
      <template v-if="activeRecipient">
        <UserAvatar :url="avatarUrl(activeRecipient.avatar)" :username="activeRecipient.username" />
        <span>{{ activeRecipient.username }}</span>
      </template>
      <span v-else class="no-chat">Выберите собеседника</span>
    </div>

    <div class="messages-box" ref="messagesBox">
      <div v-if="!activeRecipient" class="empty-chat">
        <div class="empty-icon">💬</div>
        <div class="empty-text">Выберите кому хотели бы отправить сообщение</div>
      </div>

      <template v-else-if="loadingHistory">
        <div v-for="i in 8" :key="i" class="message skeleton">
          <div class="sk-bubble shimmer"></div>
          <div class="sk-meta shimmer"></div>
        </div>
      </template>

      <div v-else-if="!messages?.length" class="empty-chat">
        <div class="empty-icon">🕊️</div>
        <div class="empty-text">Пока нет сообщений. Напишите первое.</div>
      </div>

      <div
        v-else
        v-for="(m, i) in messages"
        :key="m.id || i"
        :class="['message', isOwn(m) ? 'outgoing' : 'incoming']"
      >
        <!-- Медиафайлы -->
        <MessageMedia
          v-if="hasFiles(m)"
          :images="m.images || []"
          :videos="m.videos || []"
          :audios="m.audios || []"
        />

        <div v-if="m.text" class="msg-text">{{ m.text }}</div>

        <div class="meta">{{ formatTime(m.created_at) }}</div>
      </div>
    </div>

    <!-- Превью прикреплённых файлов + поле подписи -->
    <div v-if="attachments.length" class="attachments-panel">
      <div class="attachments-header">
        <span class="attachments-title">{{ attachments.length }} файл{{ attachments.length > 1 ? 'а' : '' }}</span>
        <button class="attachments-clear" @click="clearAttachments">✕ Очистить</button>
      </div>
      <div class="attachments-thumbs">
        <div v-for="(a, i) in attachments" :key="i" class="attachment-thumb">
          <img v-if="a.type === 'image'" :src="a.preview" class="thumb-img" />
          <div v-else class="thumb-file">
            <span class="thumb-icon">{{ fileIcon(a.type) }}</span>
            <span class="thumb-name">{{ a.file.name }}</span>
          </div>
          <button class="thumb-remove" @click="removeAttachment(i)">✕</button>
        </div>
        <!-- Добавить ещё -->
        <label class="thumb-add">
          +
          <input type="file" accept="image/*,video/*,audio/*" multiple @change="onFileSelectAuto" hidden />
        </label>
      </div>
      <div class="caption-area">
        <input
          v-model="inputText"
          ref="captionInput"
          placeholder="Добавить подпись..."
          :disabled="!activeRecipient"
          @keydown.enter="send"
        />
        <button
          class="btn btn-primary"
          :disabled="sending"
          @click="send"
        >
          {{ sending ? '...' : '→' }}
        </button>
      </div>
    </div>

    <div v-else class="chat-input-area">
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
import UserAvatar from './UserAvatar.vue'
import { avatarUrl } from '../useAuth'

const props = defineProps({
  messages: Array,
  activeRecipient: Object,
  currentUser: Object,
  isMobile: { type: Boolean, default: false },
  loadingHistory: { type: Boolean, default: false },
})
const emit = defineEmits(['send', 'back'])

const inputText = ref('')
const messagesBox = ref(null)
const captionInput = ref(null)
const attachments = ref([])
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
  return ts 
    ? new Date(ts).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    : new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
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
  files.forEach(file => {
    const preview = type === 'image' ? URL.createObjectURL(file) : null
    attachments.value.push({ file, type, preview })
  })
  showAttachMenu.value = false
  e.target.value = ''
}

function onFileSelectAuto(e) {
  const files = Array.from(e.target.files)
  files.forEach(file => {
    const type = file.type.startsWith('image') ? 'image'
      : file.type.startsWith('video') ? 'video' : 'audio'
    const preview = type === 'image' ? URL.createObjectURL(file) : null
    attachments.value.push({ file, type, preview })
  })
  e.target.value = ''
}

function removeAttachment(i) {
  const a = attachments.value[i]
  if (a.preview) URL.revokeObjectURL(a.preview)
  attachments.value.splice(i, 1)
}

function clearAttachments() {
  attachments.value.forEach(a => { if (a.preview) URL.revokeObjectURL(a.preview) })
  attachments.value = []
  inputText.value = ''
}

async function send() {
  const text = inputText.value.trim()
  if ((!text && !attachments.value.length) || !props.activeRecipient || sending.value) return

  sending.value = true
  try {
    const fileUuids = { images: [], videos: [], audios: [] }
    let totalFailed = 0

    if (attachments.value.length) {
      const imageFiles = attachments.value.filter(a => a.type === 'image').map(a => a.file)
      const videoFiles = attachments.value.filter(a => a.type === 'video').map(a => a.file)
      const audioFiles = attachments.value.filter(a => a.type === 'audio').map(a => a.file)

      if (imageFiles.length) { const r = await uploadFiles(imageFiles); fileUuids.images = r.uuids; totalFailed += r.failed }
      if (videoFiles.length) { const r = await uploadFiles(videoFiles); fileUuids.videos = r.uuids; totalFailed += r.failed }
      if (audioFiles.length) { const r = await uploadFiles(audioFiles); fileUuids.audios = r.uuids; totalFailed += r.failed }

      const totalUploaded = fileUuids.images.length + fileUuids.videos.length + fileUuids.audios.length

      // Если все файлы не загрузились и подписи нет — отменяем
      if (totalUploaded === 0 && !text) {
        showToast('Не удалось загрузить файлы. Попробуйте ещё раз.', 'error')
        return
      }

      if (totalFailed > 0)
        showToast(`${totalFailed} файл${totalFailed > 1 ? 'а' : ''} не удалось загрузить — сообщение отправлено без них`, 'warning')
    }

    emit('send', { text, fileUuids })
    inputText.value = ''
    attachments.value.forEach(a => { if (a.preview) URL.revokeObjectURL(a.preview) })
    attachments.value = []

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
.chat-area { flex: 1; display: flex; flex-direction: column; position: relative; min-height: 0; overflow: hidden; }

.chat-header {
  padding: 14px 20px;
  border-bottom: 1px solid #2a2d3a;
  font-size: 14px;
  font-weight: 600;
  color: #ccc;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
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

.messages-box {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overscroll-behavior: contain;
  background-image: radial-gradient(ellipse at 50% 0%, rgba(124,106,247,.04) 0%, transparent 70%);
}

.message {
  max-width: 75%;
  min-width: 0;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  word-break: break-word;
}

.message.skeleton {
  background: transparent;
  padding: 0;
  box-shadow: none;
  align-self: flex-start;
  max-width: 85%;
}

.sk-bubble {
  height: 38px;
  border-radius: 14px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.05);
}

.sk-meta {
  margin-top: 6px;
  height: 10px;
  width: 64px;
  border-radius: 8px;
  background: rgba(255,255,255,0.06);
}

.shimmer {
  position: relative;
  overflow: hidden;
}
.shimmer::after {
  content: "";
  position: absolute;
  top: 0; left: -160px;
  width: 160px;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(124,106,247,0.14),
    transparent
  );
  animation: shimmer 1.1s infinite;
}

@keyframes shimmer {
  to { left: 100%; }
}

@media (max-width: 900px) {
  .message { max-width: 90%; }
  .messages-box { padding: 12px; }
}

@media (max-width: 900px) and (orientation: portrait) {
  .chat-input-area, .caption-area {
    padding-bottom: max(12px, env(safe-area-inset-bottom));
  }
}

@media (max-width: 900px) and (orientation: landscape) {
  .messages-box { padding: 8px 12px; }
  .chat-header { padding: 8px 16px; }
  .chat-input-area { padding: 6px 12px; }
  .message { max-width: 80%; }
}

.message.incoming {
  background: #252838;
  color: #ddd;
  align-self: flex-start;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 2px rgba(0,0,0,.2);
}

.message.outgoing {
  background: linear-gradient(135deg, #7c6af7, #6a5ae0);
  color: #fff;
  align-self: flex-end;
  border-bottom-right-radius: 4px;
  box-shadow: 0 1px 8px rgba(124,106,247,.35);
}

.msg-text { margin-top: 4px; }

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

/* Attachments panel (caption mode) */
.attachments-panel {
  border-top: 1px solid #2a2d3a;
  background: #161824;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.attachments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px 4px;
}

.attachments-title {
  font-size: 12px;
  color: #888;
}

.attachments-clear {
  background: none;
  border: none;
  color: #e74c3c;
  font-size: 11px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
}
.attachments-clear:hover { background: rgba(231,76,60,.1); }

.attachments-thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 4px 12px 8px;
}

.attachment-thumb {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.thumb-img {
  width: 72px;
  height: 72px;
  object-fit: cover;
  display: block;
  border-radius: 8px;
}

.thumb-file {
  width: 72px;
  height: 72px;
  background: #2a2d3a;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.thumb-icon { font-size: 22px; }

.thumb-name {
  font-size: 9px;
  color: #aaa;
  max-width: 64px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
}

.thumb-remove {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(0,0,0,.7);
  border: none;
  color: #fff;
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
}
.thumb-remove:hover { background: #e74c3c; }

.thumb-add {
  width: 72px;
  height: 72px;
  background: #2a2d3a;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #666;
  cursor: pointer;
  flex-shrink: 0;
  transition: background .15s;
}
.thumb-add:hover { background: #353849; color: #aaa; }

@media (max-width: 900px) {
  .thumb-img, .thumb-file, .thumb-add {
    width: 60px;
    height: 60px;
  }
  .thumb-name { max-width: 52px; }
}

.caption-area {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 12px;
  border-top: 1px solid #2a2d3a;
}

.caption-area input {
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
.caption-area input:focus { border-color: #7c6af7; }

/* Input area */
.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid #2a2d3a;
  display: flex;
  gap: 8px;
  align-items: center;
  position: relative;
  flex-shrink: 0;
  padding-bottom: max(12px, env(safe-area-inset-bottom));
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
  flex-shrink: 0;
}
.btn:active { opacity: .75; }
@media (hover: hover) and (pointer: fine) {
  .btn:hover { opacity: .85; }
}
.btn:disabled { opacity: .4; cursor: not-allowed; }
.btn-primary { background: #7c6af7; color: #fff; }
</style>
