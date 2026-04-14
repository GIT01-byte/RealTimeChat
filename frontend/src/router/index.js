import { createRouter, createWebHistory } from 'vue-router'
import { currentUser, fetchSelfInfo } from '../useAuth'

const routes = [
  {
    path: '/',
    component: () => import('../components/AuthScreen.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/chat',
    component: () => import('../components/ChatScreen.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    component: () => import('../components/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!currentUser.value) await fetchSelfInfo()
  if (to.meta.requiresAuth && !currentUser.value) return '/'
  if (to.meta.guestOnly && currentUser.value) return '/chat'
})

export default router
