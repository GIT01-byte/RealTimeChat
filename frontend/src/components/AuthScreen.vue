<template>
  <div class="auth-screen">

    <!-- Приветственный экран -->
    <div v-if="showWelcome" class="welcome">
      <div class="welcome-icon">💬</div>
      <h1 class="welcome-title">RT Chat</h1>
      <p class="welcome-desc">{{ WELCOME_TEXT }}</p>
      <button class="btn btn-primary welcome-btn" @click="closeWelcome">Начать</button>
    </div>

    <template v-else>

    <div class="auth-tabs">
      <div :class="['auth-tab', tab === 'login' && 'active']" @click="tab = 'login'">Вход</div>
      <div :class="['auth-tab', tab === 'register' && 'active']" @click="tab = 'register'">Регистрация</div>
    </div>

    <form v-if="tab === 'login'" class="auth-form" @submit.prevent="handleLogin">
      <input v-model="username" placeholder="Имя пользователя" required />
      <input v-model="password" type="password" placeholder="Пароль" required />
      <button class="btn btn-primary" type="submit" :disabled="loading">
        {{ loading ? 'Вход...' : 'Войти' }}
      </button>
      <div class="auth-error">{{ error }}</div>
    </form>

    <form v-else class="auth-form" @submit.prevent="handleRegister">
      <!-- Аватар -->
      <label class="avatar-pick">
        <input type="file" accept="image/*" hidden @change="onAvatarPick" />
        <div class="avatar-preview">
          <img v-if="avatarPreview" :src="avatarPreview" class="avatar-preview-img" />
          <span v-else class="avatar-preview-placeholder">+📷</span>
        </div>
        <span class="avatar-pick-hint">{{ avatarFile ? avatarFile.name : 'Добавить фото (необязательно)' }}</span>
      </label>
      <input v-model="username" placeholder="Имя пользователя" required />
      <input v-model="password" type="password" placeholder="Пароль (мин. 8 символов)" required />
      <button class="btn btn-primary" type="submit" :disabled="loading">
        {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
      </button>
      <div class="auth-error">{{ error }}</div>
    </form>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { login, register } from '../useAuth'

const WELCOME_TEXT = 'Мессенджер для общения в реальном времени. Быстро, удобно, без лишнего.'
const WELCOME_STORAGE_KEY = 'rt_chat_welcome_shown'

const router = useRouter()
const tab = ref('login')
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showWelcome = ref(false)
const avatarFile = ref(null)
const avatarPreview = ref(null)

function onAvatarPick(e) {
  const file = e.target.files[0]
  if (!file) return
  if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value)
  avatarFile.value = file
  avatarPreview.value = URL.createObjectURL(file)
}

onMounted(() => {
  if (!localStorage.getItem(WELCOME_STORAGE_KEY)) {
    showWelcome.value = true
  }
})

function closeWelcome() {
  showWelcome.value = false
  localStorage.setItem(WELCOME_STORAGE_KEY, '1')
}

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(username.value, password.value)
    router.push('/chat')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка входа'
  } finally { loading.value = false }
}

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    await register(username.value, password.value, avatarFile.value)
    router.push('/chat')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка регистрации'
  } finally { loading.value = false }
}
</script>

<style scoped>
.auth-screen {
  width: 360px;
  padding: 32px;
  background: #1c1f2e;
  border-radius: 20px;
  box-shadow: 0 8px 40px rgba(0,0,0,.5), 0 0 0 1px rgba(124,106,247,.1);
}

@media (max-width: 600px) {
  .auth-screen {
    width: 100vw;
    min-height: 100dvh;
    padding: 32px 20px;
    border-radius: 0;
    box-shadow: none;
  }
}

/* ───── Welcome ───── */
.welcome {
  text-align: center;
  padding: 8px 0 32px;
}

.welcome-icon { font-size: 48px; margin-bottom: 12px; }

.welcome-title {
  font-size: 26px;
  font-weight: 700;
  color: #7c6af7;
  margin-bottom: 10px;
}

.welcome-desc {
  font-size: 14px;
  color: #aaa;
  line-height: 1.6;
  margin-bottom: 24px;
}

.welcome-btn { width: 100%; padding: 12px; font-size: 15px; }

/* ───── Auth ───── */
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

.auth-form { display: flex; flex-direction: column; gap: 12px; }

.avatar-pick {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.avatar-preview {
  width: 56px; height: 56px;
  border-radius: 50%;
  background: #2a2d3a;
  border: 2px dashed #3a3d4a;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  transition: border-color .2s;
}
.avatar-pick:hover .avatar-preview { border-color: #7c6af7; }

.avatar-preview-img {
  width: 100%; height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.avatar-preview-placeholder { font-size: 20px; }

.avatar-pick-hint {
  font-size: 12px;
  color: #666;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
