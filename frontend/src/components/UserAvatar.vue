<template>
  <div class="avatar-wrap" :style="{ width: size + 'px', height: size + 'px' }">
    <img v-if="url" :src="url" class="avatar-img" :alt="username" />
    <div v-else class="avatar-letter" :style="{ fontSize: size * 0.4 + 'px' }">
      {{ username?.[0]?.toUpperCase() }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  url:      { type: String,  default: null },
  username: { type: String,  default: '' },
  size:     { type: Number,  default: 32 },
})
</script>

<style scoped>
.avatar-wrap {
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-letter {
  width: 100%;
  height: 100%;
  background: #7c6af7;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #fff;
}
</style>
