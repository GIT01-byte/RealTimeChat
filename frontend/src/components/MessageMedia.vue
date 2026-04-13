<template>
  <div class="media-container">
    <div v-if="loading" class="media-loading">
      <span class="spinner"></span>
    </div>

    <template v-else>
      <!-- Сетка изображений (как в Telegram) -->
      <div v-if="resolvedImages.length" :class="['img-grid', `img-grid--${Math.min(resolvedImages.length, 4)}`]">
        <div
          v-for="(f, i) in resolvedImages.slice(0, 4)"
          :key="f.uuid"
          class="img-cell"
          @click="openPreview(f.s3_url)"
        >
          <img :src="f.s3_url" />
          <div v-if="i === 3 && resolvedImages.length > 4" class="img-more">
            +{{ resolvedImages.length - 4 }}
          </div>
        </div>
      </div>

      <!-- Видео -->
      <div v-for="f in resolvedVideos" :key="f.uuid" class="media-video">
        <video :src="f.s3_url" controls preload="metadata" />
      </div>

      <!-- Аудио — кастомный плеер -->
      <div v-for="f in resolvedAudios" :key="f.uuid" class="audio-player">
        <audio :ref="el => audioRefs[f.uuid] = el" :src="f.s3_url" preload="metadata"
          @timeupdate="onTimeUpdate(f.uuid)"
          @loadedmetadata="onMetaLoaded(f.uuid)"
          @ended="onEnded(f.uuid)"
        />
        <button class="audio-play" @click="togglePlay(f.uuid)">
          {{ audioState[f.uuid]?.playing ? '⏸' : '▶' }}
        </button>
        <div class="audio-body">
          <div class="audio-progress" @click="seek($event, f.uuid)">
            <div class="audio-bar" :style="{ width: progressPercent(f.uuid) + '%' }"></div>
          </div>
          <div class="audio-time">{{ formatAudioTime(f.uuid) }}</div>
        </div>
      </div>
    </template>

    <!-- Полноэкранный просмотр -->
    <Teleport to="body">
      <div v-if="previewUrl" class="preview-overlay" @click="previewUrl = null">
        <img :src="previewUrl" class="preview-img" @click.stop />
        <button class="preview-close" @click="previewUrl = null">✕</button>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { resolveFileUrls } from '../useMedia'

const props = defineProps({
  images: { type: Array, default: () => [] },
  videos: { type: Array, default: () => [] },
  audios: { type: Array, default: () => [] },
})

const loading = ref(false)
const resolvedImages = ref([])
const resolvedVideos = ref([])
const resolvedAudios = ref([])
const previewUrl = ref(null)
const audioRefs = reactive({})
const audioState = reactive({})

onMounted(async () => {
  const allUuids = [...props.images, ...props.videos, ...props.audios]
  if (!allUuids.length) return
  loading.value = true
  try {
    if (props.images.length) resolvedImages.value = await resolveFileUrls(props.images)
    if (props.videos.length) resolvedVideos.value = await resolveFileUrls(props.videos)
    if (props.audios.length) resolvedAudios.value = await resolveFileUrls(props.audios)
    resolvedAudios.value.forEach(f => {
      audioState[f.uuid] = { playing: false, current: 0, duration: 0 }
    })
  } finally {
    loading.value = false
  }
})

function openPreview(url) { previewUrl.value = url }

function togglePlay(uuid) {
  const el = audioRefs[uuid]
  if (!el) return
  if (audioState[uuid].playing) {
    el.pause()
    audioState[uuid].playing = false
  } else {
    // Останавливаем остальные
    Object.keys(audioRefs).forEach(id => {
      if (id !== uuid && audioState[id]?.playing) {
        audioRefs[id].pause()
        audioState[id].playing = false
      }
    })
    el.play()
    audioState[uuid].playing = true
  }
}

function onTimeUpdate(uuid) {
  const el = audioRefs[uuid]
  if (el) audioState[uuid].current = el.currentTime
}

function onMetaLoaded(uuid) {
  const el = audioRefs[uuid]
  if (el) audioState[uuid].duration = el.duration
}

function onEnded(uuid) {
  audioState[uuid].playing = false
  audioState[uuid].current = 0
}

function seek(e, uuid) {
  const el = audioRefs[uuid]
  if (!el) return
  const rect = e.currentTarget.getBoundingClientRect()
  const ratio = (e.clientX - rect.left) / rect.width
  el.currentTime = ratio * el.duration
}

function progressPercent(uuid) {
  const s = audioState[uuid]
  if (!s || !s.duration) return 0
  return (s.current / s.duration) * 100
}

function formatAudioTime(uuid) {
  const s = audioState[uuid]
  if (!s) return '0:00'
  const t = s.playing || s.current ? s.current : s.duration
  if (!t) return '0:00'
  const m = Math.floor(t / 60)
  const sec = Math.floor(t % 60).toString().padStart(2, '0')
  return `${m}:${sec}`
}
</script>

<style scoped>
.media-container { margin-top: 6px; }

.media-loading {
  display: flex;
  align-items: center;
  padding: 6px 0;
}

.spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,.2);
  border-top-color: #7c6af7;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Сетка изображений */
.img-grid {
  display: grid;
  gap: 2px;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 4px;
  width: min(360px, 55vw);
}

.img-grid--1 { grid-template-columns: 1fr; }
.img-grid--2 { grid-template-columns: 1fr 1fr; }
.img-grid--3 { grid-template-columns: 1fr 1fr; grid-template-rows: auto auto; }
.img-grid--3 .img-cell:first-child { grid-column: 1 / -1; }
.img-grid--4 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }

.img-cell {
  position: relative;
  overflow: hidden;
  cursor: pointer;
  aspect-ratio: 1;
}

.img-grid--1 .img-cell { aspect-ratio: 4/3; }

.img-cell img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform .2s;
}
.img-cell:hover img { transform: scale(1.03); }

.img-more {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,.55);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}

/* Видео */
.media-video { margin-bottom: 4px; }
.media-video video {
  width: min(360px, 55vw);
  border-radius: 10px;
  display: block;
}

/* Аудио плеер */
.audio-player {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(0,0,0,.2);
  border-radius: 24px;
  padding: 8px 12px;
  width: 260px;
  min-width: 260px;
  margin-bottom: 4px;
  box-sizing: border-box;
}

@media (max-width: 900px) {
  .img-grid { width: min(320px, 72vw); }
  .media-video video { width: min(320px, 72vw); }
  .audio-player { width: 220px; min-width: 220px; }
}

.audio-play {
  width: 34px; height: 34px;
  border-radius: 50%;
  background: #7c6af7;
  border: none;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: opacity .15s;
}
.audio-play:hover { opacity: .85; }

.audio-body { flex: 1; display: flex; flex-direction: column; gap: 4px; }

.audio-progress {
  height: 3px;
  background: rgba(255,255,255,.2);
  border-radius: 2px;
  cursor: pointer;
  position: relative;
}

.audio-bar {
  height: 100%;
  background: #7c6af7;
  border-radius: 2px;
  transition: width .1s linear;
}

.audio-time {
  font-size: 10px;
  opacity: .6;
  text-align: right;
}

/* Полноэкранный просмотр */
.preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  cursor: zoom-out;
}

.preview-img {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 8px;
  object-fit: contain;
  cursor: default;
}

.preview-close {
  position: fixed;
  top: 20px;
  right: 24px;
  background: rgba(255,255,255,.15);
  border: none;
  color: #fff;
  font-size: 20px;
  width: 36px; height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-close:hover { background: rgba(255,255,255,.25); }
</style>
