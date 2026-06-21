import { createRouter, createWebHistory } from 'vue-router'
import Landing from '../views/Landing.vue'
import Dashboard from '../views/Dashboard.vue'
import Chat from '../views/Chat.vue'
import LiteratureSearch from '../views/LiteratureSearch.vue'
import PaperLibrary from '../views/PaperLibrary.vue'
import PaperReview from '../views/PaperReview.vue'
import Settings from '../views/Settings.vue'
import Login from '../views/Login.vue'
import { isAuthenticated } from '../api/auth'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: Landing,
    meta: { requiresGuest: true, isLanding: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: { requiresAuth: true }
  },
  {
    path: '/memory',
    redirect: '/settings'
  },
  {
    path: '/literature',
    name: 'Literature',
    component: LiteratureSearch,
    meta: { requiresAuth: true }
  },
  {
    path: '/library',
    name: 'PaperLibrary',
    component: PaperLibrary,
    meta: { requiresAuth: true }
  },
  {
    path: '/review',
    name: 'PaperReview',
    component: PaperReview,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0, behavior: 'instant' }
  }
})

router.beforeEach((to, from, next) => {
  const authenticated = isAuthenticated()

  if (to.meta.requiresAuth && !authenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && authenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
