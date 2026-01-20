import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Chat from '../views/Chat.vue'
import LiteratureSearch from '../views/LiteratureSearch.vue'
import PaperLibrary from '../views/PaperLibrary.vue'
import PaperReview from '../views/PaperReview.vue'
import MilvusManager from '../views/MilvusManager.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Home
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat
  },
  {
    path: '/literature',
    name: 'Literature',
    component: LiteratureSearch
  },
  {
    path: '/library',
    name: 'PaperLibrary',
    component: PaperLibrary
  },
  {
    path: '/review',
    name: 'PaperReview',
    component: PaperReview
  },
  {
    path: '/milvus',
    name: 'MilvusManager',
    component: MilvusManager
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
