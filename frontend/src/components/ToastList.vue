<template>
  <div class="toast-list">
    <div
      v-for="t in toasts"
      :key="t.id"
      :class="['toast', t.type]"
    >
      {{ t.message }}
    </div>
  </div>
</template>

<script setup>
import { toasts } from '../useToast'
</script>

<style scoped>
.toast-list {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 999;
  pointer-events: none;
}

.toast {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
  background: #2a2d3a;
  box-shadow: 0 4px 16px rgba(0,0,0,.4);
  animation: fadein .2s ease;
}

.toast.warning { background: #b7791f; }
.toast.error   { background: #c0392b; }
.toast.success { background: #27ae60; }
.toast.info    { background: #2a2d3a; }

@keyframes fadein {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
