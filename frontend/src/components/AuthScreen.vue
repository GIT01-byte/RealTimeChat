<template>
  <div class="auth-screen">
    <div class="auth-logo">💬 RT Chat</div>

    <div class="auth-tabs">
      <div :class="['auth-tab', tab === 'login' && 'active']" @click="tab = 'login'">Вход</div>
      <div :class="['auth-tab', tab === 'register' && 'active']" @click="tab = 'register'">Регистрация</div>
    </div>

    <!-- Login -->
    <form v-if="tab === 'login'" class="auth-form" @submit.prevent="handleLogin">
      <input v-model="username" placeholder="Имя пользователя" required />
      <input v-model="password" type="password" placeholder="Пароль" required />
      <button class="btn btn-primary" type="submit" :disabled="loading">
        {{ loading ? 'Вход...' : 'Войти' }}
      </button>
      <div class="auth-error">{{ error }}</div>
    </form>

    <!-- Register -->
    <form v-else class="auth-form" @submit.prevent="handleRegister">
      <input v-model="username" placeholder="Имя пользователя" required />
      <input v-model="password" type="password" placeholder="Пароль (мин. 8 символов)" required />
      <button class="btn btn-primary" type="submit" :disabled="loading">
        {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
      </button>
      <div class="auth-error">{{ error }}</div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { login, register } from '../useAuth'

const emit = defineEmits(['logged-in'])

const tab = ref('login')
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(username.value, password.value)
    emit('logged-in')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка входа'
  } finally { loading.value = false }
}

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    await register(username.value, password.value)
    emit('logged-in')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка регистрации'
  } finally { loading.value = false }
}
</script>

<style scoped>
.auth-screen { width: 360px; }

.auth-logo {
  text-align: center;
  font-size: 28px;
  font-weight: 700;
  color: #7c6af7;
  margin-bottom: 24px;
  letter-spacing: 1px;
}

.auth-tabs {
  display: flex;
  border-bottom: 2px solid #2a2d3a;
  margin-bottom: 24px;
}

.auth-tab {
  flex: 1;
  padding: 10px;
  text-align: center;
  cursor: pointer;
  color: #888;
  font-size: 14px;
  transition: color .2s;
}

.auth-tab.active {
  color: #7c6af7;
  border-bottom: 2px solid #7c6af7;
  margin-bottom: -2px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.auth-form input {
  background: #1c1f2e;
  border: 1px solid #2a2d3a;
  border-radius: 8px;
  padding: 10px 14px;
  color: #e0e0e0;
  font-size: 14px;
  outline: none;
  transition: border-color .2s;
}

.auth-form input:focus { border-color: #7c6af7; }

.btn {
  padding: 10px 18px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: opacity .2s;
}
.btn:hover { opacity: .85; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
.btn-primary { background: #7c6af7; color: #fff; }

.auth-error {
  color: #e74c3c;
  font-size: 12px;
  text-align: center;
  min-height: 16px;
}
</style>
