<template>
  <Teleport to="body">
    <div class="profile-overlay" @click.self="$emit('close')">
      <div class="profile-modal">

        <button class="close-btn" @click="$emit('close')">✕</button>

        <!-- Аватар -->
        <label class="avatar-wrap">
          <input type="file" accept="image/*" hidden @change="onAvatarChange" />
          <UserAvatar :url="currentUser?.avatarUrl" :username="currentUser?.username" :size="80" />
          <div class="avatar-overlay">📷</div>
        </label>

        <div class="username-display">{{ currentUser?.username }}</div>
        <div class="role-badge">{{ currentUser?.role }}</div>

        <!-- Форма редактирования -->
        <form class="profile-form" @submit.prevent="handleUpdate">
          <label class="field-label">Имя пользователя</label>
          <input v-model="form.username" placeholder="Новое имя" :disabled="saving" />

          <div v-if="updateError" class="form-error">{{ updateError }}</div>

          <button class="btn btn-primary" type="submit" :disabled="saving || !form.username.trim()">
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </form>

        <div class="divider"></div>

        <!-- Удаление аккаунта -->
        <button class="btn btn-danger" @click="confirmDelete = true" :disabled="deleting">
          {{ deleting ? 'Удаление...' : '🗑 Удалить аккаунт' }}
        </button>

        <!-- Подтверждение удаления -->
        <div v-if="confirmDelete" class="confirm-box">
          <div class="confirm-text">Вы уверены? Это действие необратимо.</div>
          <div class="confirm-actions">
            <button class="btn btn-danger btn-sm" @click="handleDelete">Удалить</button>
            <button class="btn btn-ghost btn-sm" @click="confirmDelete = false">Отмена</button>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser, updateAvatar, updateUser, deleteUser } from '../useAuth'
import { uploadAvatar, linkFile } from '../useMedia'
import { showToast } from '../useToast'
import UserAvatar from './UserAvatar.vue'

const emit = defineEmits(['close'])
const router = useRouter()

const saving = ref(false)
const deleting = ref(false)
const confirmDelete = ref(false)
const updateError = ref('')
const form = ref({ username: currentUser.value?.username || '' })

async function onAvatarChange(e) {
  const file = e.target.files[0]
  if (!file || !currentUser.value) return
  e.target.value = ''
  try {
    const uuid = await uploadAvatar(file, currentUser.value.user_id)
    await linkFile(uuid)
    await updateUser({ avatar: uuid })
    updateAvatar(uuid)
    showToast('Аватар обновлён', 'success')
  } catch {
    showToast('Не удалось обновить аватар', 'error')
  }
}

async function handleUpdate() {
  updateError.value = ''
  if (!form.value.username.trim()) return
  saving.value = true
  try {
    await updateUser({ username: form.value.username.trim() })
    showToast('Профиль обновлён', 'success')
    emit('close')
  } catch (e) {
    updateError.value = e.response?.data?.detail || 'Ошибка обновления'
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  deleting.value = true
  try {
    await deleteUser()
    router.push('/')
  } catch {
    showToast('Не удалось удалить аккаунт', 'error')
    deleting.value = false
    confirmDelete.value = false
  }
}
</script>

<style scoped>
.profile-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.profile-modal {
  background: #1c1f2e;
  border-radius: 16px;
  padding: 32px 28px 24px;
  width: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  position: relative;
  box-shadow: 0 8px 40px rgba(0,0,0,.5), 0 0 0 1px rgba(124,106,247,.1);
}

@media (max-width: 400px) {
  .profile-modal { width: 100vw; border-radius: 16px 16px 0 0; }
  .profile-overlay { align-items: flex-end; }
}

.close-btn {
  position: absolute;
  top: 14px; right: 14px;
  background: none;
  border: none;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  line-height: 1;
}
.close-btn:hover { color: #aaa; }

.avatar-wrap {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  overflow: hidden;
  display: block;
}
.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,.5);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  opacity: 0;
  transition: opacity .15s;
  border-radius: 50%;
}
.avatar-wrap:hover .avatar-overlay { opacity: 1; }

.username-display {
  font-size: 18px;
  font-weight: 700;
  color: #e0e0e0;
}

.role-badge {
  font-size: 11px;
  color: #7c6af7;
  background: rgba(124,106,247,.12);
  padding: 2px 10px;
  border-radius: 20px;
}

.profile-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 11px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: .5px;
}

.profile-form input {
  width: 100%;
  background: #0f1117;
  border: 1px solid #2a2d3a;
  border-radius: 8px;
  padding: 10px 14px;
  color: #e0e0e0;
  font-size: 13px;
  outline: none;
  transition: border-color .2s;
  box-sizing: border-box;
}
.profile-form input:focus { border-color: #7c6af7; }
.profile-form input:disabled { opacity: .4; }

.form-error { font-size: 12px; color: #e74c3c; }

.divider {
  width: 100%;
  height: 1px;
  background: #2a2d3a;
}

.confirm-box {
  width: 100%;
  background: rgba(231,76,60,.08);
  border: 1px solid rgba(231,76,60,.2);
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.confirm-text { font-size: 13px; color: #e74c3c; text-align: center; }

.confirm-actions { display: flex; gap: 8px; justify-content: center; }

.btn {
  padding: 10px 18px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: opacity .2s;
  width: 100%;
}
.btn:hover { opacity: .85; }
.btn:disabled { opacity: .4; cursor: not-allowed; }
.btn-primary { background: #7c6af7; color: #fff; }
.btn-danger { background: rgba(231,76,60,.15); color: #e74c3c; border: 1px solid rgba(231,76,60,.3); }
.btn-ghost { background: #2a2d3a; color: #aaa; }
.btn-sm { padding: 7px 14px; font-size: 12px; width: auto; }
</style>
