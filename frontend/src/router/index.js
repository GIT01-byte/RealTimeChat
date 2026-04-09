import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../useAuth'

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

router.beforeEach((to) => {
  const token = getToken()
  if (to.meta.requiresAuth && !token) return '/'
  if (to.meta.guestOnly && token) return '/chat'
})

export default router
