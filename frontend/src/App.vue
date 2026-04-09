<template>
  <div class="app">
    <RouterView />
    <ToastList />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ToastList from './components/ToastList.vue'
import { fetchSelfInfo, getToken } from './useAuth'

const router = useRouter()

onMounted(async () => {
  if (getToken()) {
    const ok = await fetchSelfInfo()
    if (!ok) router.push('/')
  }
})
</script>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', sans-serif;
  background: #0f1117;
  color: #e0e0e0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
@media (max-width: 600px) {
  body {
    align-items: flex-start;
    height: 100dvh;
  }
}
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2d3a; border-radius: 4px; }
</style>
