<template>
  <div class="sidebar">
    <div class="sidebar-header">
      Пользователи
      <div class="header-right">
        <span class="search-icon" @click="toggleSearch" title="Поиск">🔍</span>
        <span :class="['ws-dot', wsConnected && 'connected']" title="WebSocket"></span>
      </div>
    </div>

    <!-- Search overlay -->
    <div :class="['search-overlay', searchOpen && 'open']">
      <input
        ref="searchInputRef"
        class="search-input"
        v-model="searchQuery"
        placeholder="Поиск пользователя..."
        @input="onSearch"
        @keydown.esc="closeSearch"
      />
      <div class="search-results">
        <div v-if="!searchResults.length && searchQuery" class="no-results">Никого не найдено</div>
        <div
          v-for="u in searchResults"
          :key="u.id"
          class="user-item"
          @click="selectUser(u)"
        >
          <UserAvatar :url="avatarUrl(u.avatar)" :username="u.username" />
          <span>{{ u.username }}</span>
        </div>
      </div>
    </div>

    <!-- User list -->
    <div class="user-list">
      <div
        v-for="u in users"
        :key="u.id"
        :class="['user-item', activeRecipient?.id === u.id && 'active']"
        @click="$emit('open-chat', u)"
      >
        <UserAvatar :url="avatarUrl(u.avatar)" :username="u.username" />
        <span>{{ u.username }}</span>
        <span
          :class="['online-dot', usersOnline[u.id] && 'online']"
          :title="usersOnline[u.id] ? 'онлайн' : 'офлайн'"
        ></span>
      </div>
    </div>

    <div class="sidebar-footer">
      <button class="btn btn-ghost btn-sm" @click="$emit('logout')">Выйти</button>
      <span class="me-name">{{ meName }}</span>
      <div class="my-avatar" title="Профиль" @click="showProfile = true">
        <UserAvatar :url="currentUser?.avatarUrl" :username="meName" />
        <div class="my-avatar-overlay">👤</div>
      </div>
    </div>

    <ProfileModal v-if="showProfile" @close="showProfile = false" />
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { searchUsers } from '../useChat'
import { currentUser, updateAvatar, fetchSelfInfo } from '../useAuth'
import { avatarUrl } from '../useAuth'
import { showToast } from '../useToast'
import UserAvatar from './UserAvatar.vue'
import ProfileModal from './ProfileModal.vue'

const props = defineProps({
  users: Array,
  usersOnline: Object,
  activeRecipient: Object,
  wsConnected: Boolean,
  meName: String,
})
const emit = defineEmits(['open-chat', 'logout'])

const searchOpen = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const searchInputRef = ref(null)
const showProfile = ref(false)
let searchTimer = null

async function toggleSearch() {
  searchOpen.value = !searchOpen.value
  if (searchOpen.value) {
    await nextTick()
    searchInputRef.value?.focus()
  } else {
    closeSearch()
  }
}

function closeSearch() {
  searchOpen.value = false
  searchQuery.value = ''
  searchResults.value = []
  clearTimeout(searchTimer)
}

function onSearch() {
  clearTimeout(searchTimer)
  if (!searchQuery.value.trim()) { searchResults.value = []; return }
  searchTimer = setTimeout(async () => {
    searchResults.value = await searchUsers(searchQuery.value.trim())
  }, 400)
}

function selectUser(u) {
  closeSearch()
  emit('open-chat', u)
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  min-width: 240px;
  background: #13162a;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(124,106,247,.12);
  position: relative;
  min-height: 0;
  overflow: hidden;
}

@media (max-width: 900px) {
  .sidebar {
    width: 100vw;
    min-width: 0;
    border-right: none;
  }
}

@media (max-width: 900px) and (orientation: portrait) {
  .sidebar-footer {
    padding-bottom: max(12px, env(safe-area-inset-bottom));
  }
}

@media (max-width: 900px) and (orientation: landscape) {
  .sidebar {
    width: 200px;
    min-width: 200px;
  }
}

.sidebar-header {
  padding: 16px;
  font-size: 13px;
  font-weight: 700;
  color: #7c6af7;
  border-bottom: 1px solid rgba(124,106,247,.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
  letter-spacing: .3px;
}

.header-right { display: flex; align-items: center; gap: 8px; }

.search-icon { cursor: pointer; font-size: 15px; }

.ws-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #555;
  display: inline-block;
}
.ws-dot.connected { background: #2ecc71; }

.search-overlay {
  position: absolute;
  top: 49px; left: 0; right: 0; bottom: 0;
  background: #161824;
  display: none;
  flex-direction: column;
  z-index: 10;
}
.search-overlay.open { display: flex; }

.search-input {
  width: 100%;
  padding: 8px 12px;
  background: #0f1117;
  border: none;
  border-bottom: 1px solid #2a2d3a;
  color: #e0e0e0;
  font-size: 13px;
  outline: none;
}
.search-input:focus { border-bottom-color: #7c6af7; }

.search-results { flex: 1; overflow-y: auto; padding: 8px 0; }
.no-results { padding: 12px 16px; color: #555; font-size: 12px; }

.user-list { flex: 1; overflow-y: auto; padding: 8px 0; }

.user-item {
  padding: 10px 16px;
  cursor: pointer;
  font-size: 13px;
  border-radius: 8px;
  margin: 2px 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background .15s;
}
.user-item:hover { background: #2a2d3a; }
.user-item.active {
  background: linear-gradient(90deg, rgba(124,106,247,.18), rgba(124,106,247,.08));
  color: #a89af9;
}

.online-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #555;
  flex-shrink: 0;
  margin-left: auto;
}
.online-dot.online { background: #2ecc71; }

.avatar-circle {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: #7c6af7;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; color: #fff;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(124,106,247,.12);
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(0,0,0,.15);
}

.me-name { color: #aaa; font-weight: 600; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-align: right; margin-right: 8px; }

.my-avatar {
  position: relative;
  width: 32px; height: 32px;
  border-radius: 50%;
  cursor: pointer;
  flex-shrink: 0;
  overflow: hidden;
}

.my-avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  opacity: 0;
  transition: opacity .15s;
}
.my-avatar:hover .my-avatar-overlay { opacity: 1; }

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
.btn-ghost { background: #2a2d3a; color: #aaa; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
</style>
