import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Chat from '../views/Chat.vue'
import LiteratureSearch from '../views/LiteratureSearch.vue'
import PaperLibrary from '../views/PaperLibrary.vue'
import PaperMindmap from '../views/PaperMindmap.vue'

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
    path: '/mindmap',
    name: 'PaperMindmap',
    component: PaperMindmap
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
