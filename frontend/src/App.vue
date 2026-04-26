<template>
  <div id="app">
      <button class="mobile-menu-btn" @click="toggleSidebar" v-if="!sidebarOpen && showSidebar">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>
      
      <div class="app-layout">
      <aside v-if="showSidebar" class="sidebar" :class="{ 'sidebar-open': sidebarOpen, 'sidebar-collapsed': sidebarCollapsed }">
        <div class="sidebar-header">
          <div class="logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="logo-text">ResearchGO</span>
          </div>
          <button class="sidebar-toggle" @click="toggleCollapse" type="button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline v-if="!sidebarCollapsed" points="15 18 9 12 15 6"></polyline>
              <polyline v-else points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
          <button class="sidebar-close" @click="toggleSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <nav class="sidebar-nav">
          <router-link to="/dashboard" class="sidebar-link" @click="closeSidebarOnMobile" :title="sidebarCollapsed ? 'Dashboard' : ''">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
            <span class="link-text">Dashboard</span>
          </router-link>
          
          <router-link to="/chat" class="sidebar-link" @click="closeSidebarOnMobile" :title="sidebarCollapsed ? 'Chat' : ''">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="link-text">Chat</span>
          </router-link>
          
          <router-link to="/literature" class="sidebar-link" @click="closeSidebarOnMobile" :title="sidebarCollapsed ? 'Literature Search' : ''">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
            </svg>
            <span class="link-text">Literature Search</span>
          </router-link>
          
          <router-link to="/library" class="sidebar-link" @click="closeSidebarOnMobile" :title="sidebarCollapsed ? 'Paper Library' : ''">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
            </svg>
            <span class="link-text">Paper Library</span>
          </router-link>
          
          <router-link to="/review" class="sidebar-link" @click="closeSidebarOnMobile" :title="sidebarCollapsed ? 'Paper Review' : ''">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="2"></circle>
              <path d="M12 2v4"></path>
              <path d="M12 18v4"></path>
              <path d="m4.93 4.93 2.83 2.83"></path>
              <path d="m16.24 16.24 2.83 2.83"></path>
              <path d="M2 12h4"></path>
              <path d="M18 12h4"></path>
              <path d="m4.93 19.07 2.83-2.83"></path>
              <path d="m16.24 7.76 2.83-2.83"></path>
            </svg>
            <span class="link-text">Paper Review</span>
          </router-link>
          
        </nav>
        
        <div class="sidebar-footer">
          <div class="user-info" @click="showUserMenu = !showUserMenu">
            <div class="user-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>
            <div class="user-details" v-if="!sidebarCollapsed">
              <div class="user-name">{{ currentUser?.username || '用户' }}</div>
              <div class="user-email">{{ currentUser?.email || '' }}</div>
            </div>
          </div>
          <div v-if="showUserMenu && !sidebarCollapsed" class="user-menu">
            <button class="user-menu-item" @click="handleLogout">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </aside>
      
      <div v-if="showSidebar" class="sidebar-overlay" :class="{ 'overlay-open': sidebarOpen }" @click="toggleSidebar"></div>
      
      <main class="main" :class="{ 
        'main-with-sidebar': sidebarOpen && showSidebar, 
        'main-collapsed': sidebarCollapsed && showSidebar,
        'main-no-sidebar': !showSidebar,
        'main-chat': route.path === '/chat'
      }">
        <router-view v-slot="{ Component }">
          <keep-alive :include="['Dashboard', 'Chat', 'Literature', 'PaperLibrary', 'PaperReview']">
            <component :is="Component" />
        </keep-alive>
        </router-view>
      </main>
      </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { logout, getStoredUser } from './api/auth'

const router = useRouter()
const route = useRoute()

const sidebarOpen = ref(false)
const sidebarCollapsed = ref(false)
const showUserMenu = ref(false)
const currentUser = ref(null)

// 计算是否显示侧边栏（登录页面和 Landing 页面不显示）
const showSidebar = computed(() => {
  return route.path !== '/login' && route.path !== '/'
})

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const toggleCollapse = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const closeSidebarOnMobile = () => {
  if (window.innerWidth <= 1024) {
    sidebarOpen.value = false
  }
}

const handleResize = () => {
  if (window.innerWidth > 1024) {
    sidebarOpen.value = true
  } else {
    sidebarOpen.value = false
    sidebarCollapsed.value = false
  }
}

const handleLogout = async () => {
  showUserMenu.value = false
  try {
    await logout()
  } catch (error) {
    console.error('登出失败:', error)
    // 即使失败也清除本地存储
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }
}

// 点击外部关闭用户菜单
const handleClickOutside = (event) => {
  if (!event.target.closest('.sidebar-footer')) {
    showUserMenu.value = false
  }
}

// 加载用户信息
const loadUserInfo = () => {
  const user = getStoredUser()
  if (user) {
    currentUser.value = user
  }
}

onMounted(() => {
  if (window.innerWidth > 1024) {
    sidebarOpen.value = true
  }
  window.addEventListener('resize', handleResize)
  document.addEventListener('click', handleClickOutside)
  loadUserInfo()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: transparent;
  position: relative;
}

.mobile-menu-btn {
  display: none;
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 300;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(8, 13, 28, 0.84);
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mobile-menu-btn:hover {
  border-color: var(--border-glow);
  color: var(--accent-primary);
  box-shadow: var(--glow-primary);
}

.app-layout {
  display: flex;
  flex: 1;
  position: relative;
}

.sidebar {
  width: 232px;
  background:
    linear-gradient(180deg, rgba(8, 13, 28, 0.96), rgba(10, 16, 32, 0.92)),
    linear-gradient(90deg, rgba(56, 189, 248, 0.08), transparent);
  border-right: 1px solid var(--border-primary);
  box-shadow: 18px 0 50px rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(22px);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 200;
  transition: width 0.2s ease, transform 0.2s ease;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-collapsed {
  width: 80px;
}

.sidebar-header {
  padding: 24px 16px;
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.86), rgba(30, 41, 59, 0.38));
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 800;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  flex: 1;
  min-width: 0;
}

.logo svg {
  color: var(--accent-primary);
  flex-shrink: 0;
  filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.52));
}

.logo-text {
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
}

.sidebar-collapsed .logo-text {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.sidebar-collapsed .sidebar-header {
  padding: 22px 12px;
  justify-content: center;
}

.sidebar-collapsed .logo {
  flex: 0 0 auto;
  width: 44px;
  height: 44px;
  justify-content: center;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.62);
  border: 1px solid rgba(56, 189, 248, 0.18);
  -webkit-text-fill-color: currentColor;
}

.sidebar-collapsed .logo svg {
  width: 24px;
  height: 24px;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.78);
  color: var(--accent-primary);
  border: 1px solid var(--border-primary);
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
  margin-left: auto;
}

.sidebar-toggle:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
}

.sidebar-collapsed .sidebar-toggle {
  position: absolute;
  right: 6px;
  top: 50%;
  width: 24px;
  height: 24px;
  margin-left: 0;
  opacity: 0;
  transform: translateY(-50%);
  pointer-events: none;
}

.sidebar-collapsed:hover .sidebar-toggle,
.sidebar-collapsed .sidebar-toggle:focus-visible {
  opacity: 1;
  pointer-events: auto;
}

.sidebar-close {
  display: none;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.78);
  color: var(--accent-primary);
  border: 1px solid var(--border-primary);
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
  margin-left: 8px;
}

.sidebar-close:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
}

.sidebar-nav {
  flex: 1;
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.sidebar-collapsed .sidebar-nav {
  align-items: center;
  padding: 24px 10px;
  gap: 10px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 15px;
  font-weight: 650;
  transition: all 0.3s ease;
  position: relative;
  justify-content: flex-start;
  border: 1px solid transparent;
}

.sidebar-collapsed .sidebar-link {
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  gap: 0;
  border-radius: 12px;
}

.sidebar-link:hover {
  background: rgba(56, 189, 248, 0.08);
  color: var(--accent-primary);
  border-color: rgba(56, 189, 248, 0.24);
  box-shadow: var(--glow-primary);
}

.sidebar-link.router-link-active {
  background: var(--gradient-primary);
  color: white;
  box-shadow: 0 14px 30px rgba(56, 189, 248, 0.2);
  border-color: transparent;
}

.sidebar-link svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.link-text {
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
}

.sidebar-collapsed .link-text {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.sidebar-collapsed .sidebar-footer {
  padding: 14px 10px;
}

.sidebar-collapsed .user-info {
  width: 44px;
  height: 52px;
  justify-content: center;
  gap: 0;
  padding: 0;
  border-radius: 12px;
  background: rgba(8, 13, 28, 0.62);
}

.sidebar-collapsed .user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-primary);
  background: rgba(15, 23, 42, 0.58);
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(8, 13, 28, 0.68);
  border: 1px solid var(--border-primary);
  transition: all 0.3s ease;
  cursor: pointer;
}

.user-info:hover {
  border-color: var(--border-glow);
  box-shadow: var(--glow-primary);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 9px;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
  box-shadow: var(--glow-primary);
}

.user-details {
  flex: 1;
  min-width: 0;
  opacity: 1;
  transition: opacity 0.3s ease;
}

.sidebar-collapsed .user-details {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  line-height: 1.2;
}

.user-email {
  font-size: 12px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-menu {
  position: absolute;
  bottom: 100%;
  left: 16px;
  right: 16px;
  margin-bottom: 8px;
  background: rgba(15, 23, 42, 0.94);
  backdrop-filter: blur(18px);
  border-radius: 10px;
  box-shadow: var(--shadow-lg), var(--glow-primary);
  border: 1px solid var(--border-glow);
  overflow: hidden;
  z-index: 10;
}

.user-menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.user-menu-item:hover {
  background: rgba(102, 126, 234, 0.1);
  color: var(--accent-primary);
}

.user-menu-item svg {
  flex-shrink: 0;
}

.sidebar-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(2, 6, 23, 0.7);
  backdrop-filter: blur(8px);
  z-index: 190;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.overlay-open {
  opacity: 1;
  pointer-events: all;
}

.main {
  flex: 1;
  margin-left: 232px;
  max-width: calc(100% - 232px);
  padding: 34px 28px;
  transition: margin-left 0.2s ease, max-width 0.2s ease;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth;
}

/* Scrollbar for main */
.main::-webkit-scrollbar {
  width: 8px;
}

.main::-webkit-scrollbar-track {
  background: transparent;
}

.main::-webkit-scrollbar-thumb {
  background: var(--accent-primary);
  border-radius: 4px;
}

.main::-webkit-scrollbar-thumb:hover {
  background: var(--accent-secondary);
}

.main-with-sidebar {
  margin-left: 232px;
}

.main-collapsed {
  margin-left: 80px;
  max-width: calc(100% - 80px);
}

.main-no-sidebar {
  margin-left: 0;
  max-width: 100%;
  padding: 0;
  height: auto;
  overflow-y: auto;
  overflow-x: hidden;
}

.main-chat {
  padding: 0;
  overflow: hidden;
}

@media (max-width: 1024px) {
  .mobile-menu-btn {
    display: flex;
  }
  
  .sidebar {
    transform: translateX(-100%);
    width: 240px;
  }
  
  .sidebar-open {
    transform: translateX(0);
  }

  .sidebar-collapsed {
    width: 240px;
  }
  
  .sidebar-close {
    display: flex;
  }
  
  .sidebar-overlay {
    display: block;
  }
  
  .main {
    margin-left: 0;
    max-width: 100%;
    padding: 32px 20px;
    height: 100vh;
  }
  
  .main-with-sidebar {
    margin-left: 0;
  }

  .main-collapsed {
    margin-left: 0;
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .mobile-menu-btn {
    top: 16px;
    left: 16px;
    width: 44px;
    height: 44px;
  }
  
  .sidebar {
    width: 220px;
  }
  
  .logo span {
    font-size: 16px;
  }
  
  .user-details {
    display: block;
  }
  
  .user-name {
    font-size: 13px;
  }
  
  .user-email {
    font-size: 11px;
  }
}
</style>
