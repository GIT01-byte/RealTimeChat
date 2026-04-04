<template>
  <div class="app">
    <AuthScreen v-if="!isLoggedIn" @logged-in="onLoggedIn" />
    <ChatScreen v-else @logout="onLogout" />
    <ToastList />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AuthScreen from './components/AuthScreen.vue'
import ChatScreen from './components/ChatScreen.vue'
import ToastList from './components/ToastList.vue'
import { currentUser, fetchSelfInfo, getToken } from './useAuth'

const isLoggedIn = ref(false)

onMounted(async () => {
  if (getToken()) {
    const ok = await fetchSelfInfo()
    if (ok) isLoggedIn.value = true
  }
})

function onLoggedIn() { isLoggedIn.value = true }
function onLogout() { isLoggedIn.value = false }
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
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2d3a; border-radius: 4px; }
</style>
