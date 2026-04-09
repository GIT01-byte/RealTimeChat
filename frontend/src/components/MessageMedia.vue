<template>
  <div class="media-container">
    <div v-if="loading" class="media-loading">⏳ Загрузка файлов...</div>

    <template v-else>
      <!-- Изображения -->
      <div v-if="resolvedImages.length" class="media-grid">
        <img
          v-for="f in resolvedImages"
          :key="f.uuid"
          :src="f.s3_url"
          class="media-image"
          @click="openPreview(f.s3_url)"
        />
      </div>

      <!-- Видео -->
      <div v-for="f in resolvedVideos" :key="f.uuid" class="media-video">
        <video :src="f.s3_url" controls preload="metadata" />
      </div>

      <!-- Аудио -->
      <div v-for="f in resolvedAudios" :key="f.uuid" class="media-audio">
        <audio :src="f.s3_url" controls />
      </div>
    </template>

    <!-- Превью изображения -->
    <div v-if="previewUrl" class="preview-overlay" @click="previewUrl = null">
      <img :src="previewUrl" class="preview-img" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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

onMounted(async () => {
  const allUuids = [...props.images, ...props.videos, ...props.audios]
  if (!allUuids.length) return

  loading.value = true
  try {
    if (props.images.length) resolvedImages.value = await resolveFileUrls(props.images)
    if (props.videos.length) resolvedVideos.value = await resolveFileUrls(props.videos)
    if (props.audios.length)  resolvedAudios.value  = await resolveFileUrls(props.audios)
  } finally {
    loading.value = false
  }
})

function openPreview(url) {
  previewUrl.value = url
}
</script>

<style scoped>
.media-container { margin-top: 6px; }

.media-loading { font-size: 12px; color: #888; padding: 4px 0; }

.media-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 4px;
}

.media-image {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity .2s;
}
.media-image:hover { opacity: .85; }

.media-video video {
  width: 100%;
  max-width: 280px;
  border-radius: 8px;
  margin-bottom: 4px;
}

.media-audio audio {
  width: 100%;
  max-width: 280px;
  margin-bottom: 4px;
}

/* Preview */
.preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  cursor: zoom-out;
}

.preview-img {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 8px;
  object-fit: contain;
}
</style>
