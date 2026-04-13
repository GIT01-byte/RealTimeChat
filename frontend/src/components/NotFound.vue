<template>
  <div class="not-found">
    <div class="code">404</div>
    <div class="title">Страница не найдена</div>
    <div class="desc">Такой страницы не существует или она была удалена</div>
    <button class="btn" @click="goHome">← На главную</button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { getToken } from '../useAuth'

const router = useRouter()

function goHome() {
  router.push(getToken() ? '/chat' : '/')
}
</script>

<style scoped>
.not-found {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.code {
  font-size: 96px;
  font-weight: 700;
  background: linear-gradient(135deg, #7c6af7, #a89af9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.title {
  font-size: 22px;
  font-weight: 600;
  color: #e0e0e0;
}

.desc {
  font-size: 14px;
  color: #666;
}

.btn {
  margin-top: 8px;
  padding: 10px 24px;
  background: #7c6af7;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity .2s;
}
.btn:hover { opacity: .85; }
</style>
