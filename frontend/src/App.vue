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
import { fetchSelfInfo } from './useAuth'

const router = useRouter()

onMounted(async () => {
  const ok = await fetchSelfInfo()
  if (!ok) router.push('/')
})
</script>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', sans-serif;
  background: #0f1117;
  background-image:
    radial-gradient(ellipse at 20% 50%, rgba(124, 106, 247, 0.07) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 20%, rgba(124, 106, 247, 0.05) 0%, transparent 50%);
  color: #e0e0e0;
  height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
@media (max-width: 900px) {
  body { align-items: flex-start; }
}
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2d3a; border-radius: 4px; }
</style>
