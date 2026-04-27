import { computed, ref } from 'vue'

const toasts = ref([])
let nextId = 0

function dismissToast(id) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

// type: info|success -> bottom-right (calm)
// type: warning|error -> top-right (alarm)
function defaultPosition(type) {
  return (type === 'error' || type === 'warning') ? 'top-right' : 'bottom-right'
}

function normalizeToastArgs(messageOrOptions, type = 'info', duration = 4000) {
  if (typeof messageOrOptions === 'string') {
    return { message: messageOrOptions, type, duration, position: defaultPosition(type) }
  }
  const msg = messageOrOptions?.message ?? ''
  const t = messageOrOptions?.type ?? type
  const d = messageOrOptions?.duration ?? duration
  const p = messageOrOptions?.position ?? defaultPosition(t)
  return { message: msg, type: t, duration: d, position: p }
}

function showToast(messageOrOptions, type = 'info', duration = 4000) {
  const { message, position, type: normalizedType, duration: normalizedDuration } =
    normalizeToastArgs(messageOrOptions, type, duration)

  const id = nextId++
  toasts.value.push({ id, message, type: normalizedType, position })
  setTimeout(() => {
    dismissToast(id)
  }, normalizedDuration)
}

const pendingRequests = ref(0)
const isLoading = computed(() => pendingRequests.value > 0)

function beginRequest() {
  pendingRequests.value++
}

function endRequest() {
  pendingRequests.value = Math.max(0, pendingRequests.value - 1)
}

 export { toasts, showToast, dismissToast, pendingRequests, isLoading, beginRequest, endRequest }
