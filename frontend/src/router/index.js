import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Chat from '../views/Chat.vue'
import LiteratureSearch from '../views/LiteratureSearch.vue'
import PaperLibrary from '../views/PaperLibrary.vue'
import PaperReview from '../views/PaperReview.vue'
import MilvusManager from '../views/MilvusManager.vue'
import Login from '../views/Login.vue'
import { isAuthenticated } from '../api/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: { requiresAuth: true }
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
    path: '/milvus',
    name: 'MilvusManager',
    component: MilvusManager,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 如果有保存的位置（浏览器前进/后退）
    if (savedPosition) {
      return savedPosition
    }
    // 路由切换时始终滚动到顶部
    return { top: 0, behavior: 'instant' }
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authenticated = isAuthenticated()

  // 如果路由需要认证
  if (to.meta.requiresAuth && !authenticated) {
    next('/login')
  }
  // 如果已登录访问登录页，重定向到首页
  else if (to.meta.requiresGuest && authenticated) {
    next('/')
  }
  else {
    next()
  }
})

export default router
