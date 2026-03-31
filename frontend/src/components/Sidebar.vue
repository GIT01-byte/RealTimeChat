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
          <div class="avatar-circle">{{ u.username[0].toUpperCase() }}</div>
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
        <div class="avatar-circle">{{ u.username[0].toUpperCase() }}</div>
        <span>{{ u.username }}</span>
        <span
          :class="['online-dot', usersOnline[u.id] && 'online']"
          :title="usersOnline[u.id] ? 'онлайн' : 'офлайн'"
        ></span>
      </div>
    </div>

    <div class="sidebar-footer">
      <span class="me-name">{{ meName }}</span>
      <button class="btn btn-ghost btn-sm" @click="$emit('logout')">Выйти</button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { searchUsers } from '../useChat'

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
  background: #161824;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #2a2d3a;
  position: relative;
}

.sidebar-header {
  padding: 16px;
  font-size: 13px;
  font-weight: 700;
  color: #7c6af7;
  border-bottom: 1px solid #2a2d3a;
  display: flex;
  align-items: center;
  justify-content: space-between;
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
.user-item.active { background: #2e2b4a; color: #7c6af7; }

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
  border-top: 1px solid #2a2d3a;
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.me-name { color: #aaa; font-weight: 600; }

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
