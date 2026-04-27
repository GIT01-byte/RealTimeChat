<template>
  <!-- Errors / warnings (top-right) -->
  <div class="toast-stack top-right" aria-live="polite">
    <div
      v-for="t in topRight"
      :key="t.id"
      :class="['toast', t.type]"
    >
      <div class="toast-body">{{ t.message }}</div>
      <button class="toast-close" type="button" aria-label="Закрыть" @click="dismissToast(t.id)">✕</button>
    </div>
  </div>

  <!-- Info / success (bottom-right) -->
  <div class="toast-stack bottom-right" aria-live="polite">
    <div
      v-for="t in bottomRight"
      :key="t.id"
      :class="['toast', t.type]"
    >
      <div class="toast-body">{{ t.message }}</div>
      <button class="toast-close" type="button" aria-label="Закрыть" @click="dismissToast(t.id)">✕</button>
    </div>
  </div>

  <!-- Global loader (bottom-center) -->
  <div v-if="isLoading" class="global-loader" aria-live="polite" aria-label="Загрузка">
    <span class="spinner" />
    <span class="loader-text">Загрузка…</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { dismissToast, isLoading, toasts } from '../useToast'

const topRight = computed(() => toasts.value.filter(t => t.position === 'top-right'))
const bottomRight = computed(() => toasts.value.filter(t => t.position === 'bottom-right'))
</script>

<style scoped>
.toast-stack {
  position: fixed;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 999;
  pointer-events: none;
}

.toast-stack.top-right {
  top: 18px;
  right: 18px;
  align-items: flex-end;
}

.toast-stack.bottom-right {
  bottom: max(18px, env(safe-area-inset-bottom));
  right: 18px;
  align-items: flex-end;
}

.toast {
  max-width: min(360px, calc(100vw - 36px));
  padding: 10px 12px 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 560;
  line-height: 1.35;
  letter-spacing: 0.15px;
  color: #fff;
  background: rgba(42, 45, 58, 0.92);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 4px 16px rgba(0,0,0,.4);
  animation: fadein .2s ease;
  pointer-events: auto;
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.toast-body {
  flex: 1;
  min-width: 0;
}

.toast-close {
  border: none;
  background: rgba(0,0,0,0.22);
  color: rgba(255,255,255,0.92);
  width: 22px;
  height: 22px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  line-height: 22px;
  text-align: center;
  padding: 0;
  flex-shrink: 0;
}
.toast-close:active { transform: scale(0.96); }

.toast.info    { background: rgba(42, 45, 58, 0.92); }
.toast.success { background: rgba(39, 174, 96, 0.92); }
.toast.warning { background: rgba(183, 121, 31, 0.92); }
.toast.error   { background: rgba(192, 57, 43, 0.92); }

.global-loader {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: max(14px, env(safe-area-inset-bottom));
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(28, 31, 46, 0.92);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 6px 26px rgba(0,0,0,.45);
  z-index: 1000;
  pointer-events: none;
}

.spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.18);
  border-top-color: rgba(124, 106, 247, 0.95);
  animation: spin .8s linear infinite;
}

.loader-text {
  font-size: 12px;
  color: rgba(224,224,224,0.92);
  letter-spacing: 0.2px;
}

@keyframes fadein {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 600px) {
  .toast-stack.top-right,
  .toast-stack.bottom-right {
    left: 12px;
    right: 12px;
    align-items: stretch;
  }
  .toast-stack.top-right { top: max(12px, env(safe-area-inset-top)); }
  .toast-stack.bottom-right { bottom: max(12px, env(safe-area-inset-bottom)); }
  .toast { max-width: 100%; }
  .global-loader {
    bottom: max(10px, env(safe-area-inset-bottom));
    max-width: calc(100vw - 24px);
  }
}
</style>
