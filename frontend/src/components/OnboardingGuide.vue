<template>
  <Teleport to="body">
    <div class="onboarding-overlay">
      <!-- Spotlight подсветка -->
      <svg class="spotlight" v-if="current.spotlight">
        <defs>
          <mask id="spotlight-mask">
            <rect width="100%" height="100%" fill="white" />
            <rect
              :x="spotlight.x" :y="spotlight.y"
              :width="spotlight.w" :height="spotlight.h"
              :rx="spotlight.r"
              fill="black"
            />
          </mask>
        </defs>
        <rect width="100%" height="100%" fill="rgba(0,0,0,0.7)" mask="url(#spotlight-mask)" />
      </svg>
      <div v-else class="overlay-bg"></div>

      <!-- Карточка подсказки -->
      <Transition name="card">
        <div
          class="guide-card"
          :style="cardStyle"
          :key="step"
        >
          <div class="guide-step">{{ step + 1 }} / {{ steps.length }}</div>
          <div class="guide-icon">{{ current.icon }}</div>
          <div class="guide-title">{{ current.title }}</div>
          <div class="guide-desc">{{ current.desc }}</div>

          <div class="guide-actions">
            <button v-if="step > 0" class="btn btn-ghost" @click="prev">← Назад</button>
            <button class="btn btn-primary" @click="next">
              {{ step === steps.length - 1 ? 'Начать! 🎉' : 'Далее →' }}
            </button>
          </div>

          <!-- Точки прогресса -->
          <div class="guide-dots">
            <span
              v-for="(_, i) in steps"
              :key="i"
              :class="['dot', i === step && 'active']"
              @click="step = i"
            ></span>
          </div>
        </div>
      </Transition>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const emit = defineEmits(['done'])

const steps = [
  {
    icon: '👋',
    title: 'Добро пожаловать!',
    desc: 'Это RT Chat — мессенджер реального времени. Давай покажем как всё устроено.',
    spotlight: null,
    pos: 'center',
  },
  {
    icon: '👥',
    title: 'Список пользователей',
    desc: 'Слева — все зарегистрированные пользователи. Зелёная точка означает что человек онлайн прямо сейчас.',
    spotlight: 'sidebar',
    pos: 'right',
  },
  {
    icon: '🔍',
    title: 'Поиск',
    desc: 'Нажми на 🔍 в шапке сайдбара чтобы найти пользователя по имени.',
    spotlight: 'search',
    pos: 'right',
  },
  {
    icon: '💬',
    title: 'Начать чат',
    desc: 'Нажми на любого пользователя — откроется диалог. Сообщения доставляются мгновенно через WebSocket.',
    spotlight: null,
    pos: 'center',
  },
  {
    icon: '📎',
    title: 'Медиафайлы',
    desc: 'Нажми 📎 в поле ввода чтобы прикрепить фото, видео или аудио. Можно добавить подпись.',
    spotlight: 'input',
    pos: 'top',
  },
  {
    icon: '👤',
    title: 'Твой профиль',
    desc: 'Нажми на свой аватар внизу слева — откроется профиль. Там можно сменить имя, аватар или удалить аккаунт.',
    spotlight: 'avatar',
    pos: 'top',
  },
]

const step = ref(0)
const current = computed(() => steps[step.value])
const spotlightRect = ref({ x: 0, y: 0, w: 0, h: 0, r: 0 })

const spotlight = computed(() => spotlightRect.value)

const cardStyle = computed(() => {
  const pos = current.value.pos
  if (pos === 'center') return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }
  if (pos === 'right')  return { top: '50%', left: 'calc(50% + 20px)', transform: 'translateY(-50%)' }
  if (pos === 'top')    return { bottom: '120px', left: '50%', transform: 'translateX(-50%)' }
  return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }
})

function getRect(selector) {
  const el = document.querySelector(selector)
  if (!el) return null
  const r = el.getBoundingClientRect()
  return { x: r.left - 6, y: r.top - 6, w: r.width + 12, h: r.height + 12, r: 10 }
}

const SPOTLIGHT_MAP = {
  sidebar: '.sidebar',
  search:  '.search-icon',
  input:   '.chat-input-area',
  avatar:  '.my-avatar',
}

function updateSpotlight() {
  const key = current.value.spotlight
  if (!key) return
  const rect = getRect(SPOTLIGHT_MAP[key])
  if (rect) spotlightRect.value = rect
}

function next() {
  if (step.value < steps.length - 1) {
    step.value++
    updateSpotlight()
  } else {
    emit('done')
  }
}

function prev() {
  if (step.value > 0) {
    step.value--
    updateSpotlight()
  }
}

onMounted(() => updateSpotlight())
</script>

<style scoped>
.onboarding-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  pointer-events: all;
}

.overlay-bg {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,.7);
}

.spotlight {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.guide-card {
  position: absolute;
  background: #1c1f2e;
  border-radius: 16px;
  padding: 28px 24px 20px;
  width: 300px;
  box-shadow: 0 8px 40px rgba(0,0,0,.6), 0 0 0 1px rgba(124,106,247,.15);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  z-index: 2001;
}

@media (max-width: 400px) {
  .guide-card {
    width: calc(100vw - 32px);
    left: 16px !important;
    transform: none !important;
    bottom: 24px !important;
    top: auto !important;
  }
}

.guide-step {
  font-size: 11px;
  color: #555;
  letter-spacing: .5px;
}

.guide-icon { font-size: 40px; line-height: 1; }

.guide-title {
  font-size: 16px;
  font-weight: 700;
  color: #e0e0e0;
  text-align: center;
}

.guide-desc {
  font-size: 13px;
  color: #888;
  text-align: center;
  line-height: 1.6;
}

.guide-actions {
  display: flex;
  gap: 8px;
  width: 100%;
  margin-top: 4px;
}

.guide-dots {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #2a2d3a;
  cursor: pointer;
  transition: background .2s, transform .2s;
}
.dot.active { background: #7c6af7; transform: scale(1.3); }

.btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: opacity .2s;
}
.btn:hover { opacity: .85; }
.btn-primary { background: #7c6af7; color: #fff; }
.btn-ghost { background: #2a2d3a; color: #aaa; }

/* Анимация карточки */
.card-enter-active, .card-leave-active { transition: opacity .2s, transform .2s; }
.card-enter-from { opacity: 0; transform: translate(-50%, calc(-50% + 12px)); }
.card-leave-to   { opacity: 0; transform: translate(-50%, calc(-50% - 12px)); }
</style>
