<template>
  <div class="login-container">
    <!-- Background Animation -->
    <div class="background-animation">
      <div class="grid-overlay"></div>
      <div class="floating-particles">
        <div v-for="i in 20" :key="i" class="particle" :style="getParticleStyle(i)"></div>
      </div>
    </div>

    <!-- Login Card -->
    <div class="login-card">
      <!-- Logo Section -->
      <div class="logo-section">
        <div class="logo-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="url(#logoGradient)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="url(#logoGradient)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="url(#logoGradient)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#00ff88;stop-opacity:1" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="logo-text">ResearchGO</h1>
        <p class="logo-subtitle">Neural Research Assistant</p>
      </div>

      <!-- Tab Switcher -->
      <div class="tab-switcher">
        <button 
          :class="['tab-btn', { active: isLogin }]" 
          @click="switchTab(true)"
          type="button"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
            <polyline points="10 17 15 12 10 7"></polyline>
            <line x1="15" y1="12" x2="3" y2="12"></line>
          </svg>
          <span>登录</span>
        </button>
        <button 
          :class="['tab-btn', { active: !isLogin }]" 
          @click="switchTab(false)"
          type="button"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="8.5" cy="7" r="4"></circle>
            <line x1="20" y1="8" x2="20" y2="14"></line>
            <line x1="23" y1="11" x2="17" y2="11"></line>
          </svg>
          <span>注册</span>
        </button>
        <div class="tab-indicator" :class="{ 'tab-register': !isLogin }"></div>
      </div>

      <!-- Forms -->
      <div class="forms-container">
        <!-- 登录表单 -->
        <form v-show="isLogin" @submit.prevent="handleLogin" class="auth-form">
          <div class="form-group">
            <label for="login-username">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              用户名或邮箱
            </label>
            <div class="input-wrapper">
              <input
                id="login-username"
                v-model="loginForm.username"
                type="text"
                placeholder="Enter your username or email"
                required
                autocomplete="username"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="login-password">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
              密码
            </label>
            <div class="input-wrapper">
              <input
                id="login-password"
                v-model="loginForm.password"
                type="password"
                placeholder="Enter your password"
                required
                autocomplete="current-password"
              />
            </div>
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="!loading">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
                <polyline points="10 17 15 12 10 7"></polyline>
                <line x1="15" y1="12" x2="3" y2="12"></line>
              </svg>
              启动神经连接
            </span>
            <span v-else class="loading-text">
              <span class="spinner"></span>
              连接中...
            </span>
          </button>
        </form>

        <!-- 注册表单 -->
        <form v-show="!isLogin" @submit.prevent="handleRegister" class="auth-form">
          <div class="form-group">
            <label for="register-username">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              用户名
            </label>
            <div class="input-wrapper">
              <input
                id="register-username"
                v-model="registerForm.username"
                type="text"
                placeholder="Choose a unique username"
                required
                minlength="3"
                maxlength="50"
                autocomplete="username"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="register-email">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                <polyline points="22,6 12,13 2,6"></polyline>
              </svg>
              邮箱
            </label>
            <div class="input-wrapper">
              <input
                id="register-email"
                v-model="registerForm.email"
                type="email"
                placeholder="Enter your email address"
                required
                autocomplete="email"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="register-password">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
              密码
            </label>
            <div class="input-wrapper">
              <input
                id="register-password"
                v-model="registerForm.password"
                type="password"
                placeholder="At least 6 characters"
                required
                minlength="6"
                autocomplete="new-password"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="register-confirm-password">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              确认密码
            </label>
            <div class="input-wrapper">
              <input
                id="register-confirm-password"
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="Confirm your password"
                required
                autocomplete="new-password"
              />
            </div>
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="!loading">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="8.5" cy="7" r="4"></circle>
                <line x1="20" y1="8" x2="20" y2="14"></line>
                <line x1="23" y1="11" x2="17" y2="11"></line>
              </svg>
              创建神经账户
            </span>
            <span v-else class="loading-text">
              <span class="spinner"></span>
              初始化中...
            </span>
          </button>
        </form>
      </div>

      <!-- Error Message -->
      <transition name="error-fade">
        <div v-if="error" class="error-message">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          {{ error }}
        </div>
      </transition>

      <!-- Footer -->
      <div class="card-footer">
        <div class="footer-indicator">
          <span class="status-dot"></span>
          <span class="status-text">SYSTEM ONLINE</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, register } from '../api/auth'

const router = useRouter()
const isLogin = ref(true)
const loading = ref(false)
const error = ref('')

const loginForm = ref({
  username: '',
  password: ''
})

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const switchTab = (toLogin) => {
  isLogin.value = toLogin
  error.value = ''
}

const getParticleStyle = (index) => {
  const size = Math.random() * 4 + 2
  const delay = Math.random() * 20
  const duration = Math.random() * 10 + 20
  const left = Math.random() * 100
  
  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`
  }
}

const handleLogin = async () => {
  error.value = ''
  loading.value = true

  try {
    const response = await login(loginForm.value)
    
    // 保存token和用户信息
    localStorage.setItem('token', response.access_token)
    localStorage.setItem('user', JSON.stringify(response.user))
    
    // 跳转到首页
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || '神经连接失败，请检查认证信息'
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  error.value = ''
  
  // 验证密码一致性
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    error.value = '密码确认不匹配'
    return
  }

  loading.value = true

  try {
    const response = await register({
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password
    })
    
    // 保存token和用户信息
    localStorage.setItem('token', response.access_token)
    localStorage.setItem('user', JSON.stringify(response.user))
    
    // 跳转到首页
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || '账户创建失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary, #0a0e1a);
  padding: 24px;
  position: relative;
  overflow: hidden;
}

/* Background Animation */
.background-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(102, 126, 234, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(102, 126, 234, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.floating-particles {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.particle {
  position: absolute;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.8), transparent);
  border-radius: 50%;
  animation: float linear infinite;
}

@keyframes float {
  0% {
    transform: translateY(100vh) scale(0);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100vh) scale(1);
    opacity: 0;
  }
}

/* Login Card */
.login-card {
  background: rgba(19, 24, 41, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-primary, rgba(102, 126, 234, 0.2));
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 
              0 0 40px rgba(102, 126, 234, 0.15);
  padding: 48px;
  width: 100%;
  max-width: 480px;
  position: relative;
  z-index: 1;
  animation: cardEnter 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(40px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Logo Section */
.logo-section {
  text-align: center;
  margin-bottom: 40px;
}

.logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background: var(--bg-secondary, rgba(26, 31, 58, 0.8));
  border: 2px solid var(--border-glow, rgba(102, 126, 234, 0.3));
  border-radius: 20px;
  margin-bottom: 20px;
  box-shadow: var(--glow-primary, 0 0 30px rgba(102, 126, 234, 0.3));
  animation: logoPulse 3s ease-in-out infinite;
}

@keyframes logoPulse {
  0%, 100% {
    box-shadow: 0 0 30px rgba(102, 126, 234, 0.3);
  }
  50% {
    box-shadow: 0 0 50px rgba(102, 126, 234, 0.5);
  }
}

.logo-text {
  font-size: 32px;
  font-weight: 700;
  background: var(--gradient-primary, linear-gradient(135deg, #667eea 0%, #00ff88 100%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.logo-subtitle {
  font-size: 13px;
  color: var(--text-tertiary, #6b7280);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 500;
}

/* Tab Switcher */
.tab-switcher {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  background: var(--bg-secondary, rgba(26, 31, 58, 0.6));
  border: 1px solid var(--border-primary, rgba(102, 126, 234, 0.1));
  border-radius: 12px;
  padding: 6px;
  margin-bottom: 32px;
}

.tab-btn {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border: none;
  background: transparent;
  color: var(--text-tertiary, #6b7280);
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-btn:hover {
  color: var(--text-secondary, #9ca3af);
}

.tab-btn.active {
  color: white;
}

.tab-btn svg {
  transition: transform 0.3s ease;
}

.tab-btn.active svg {
  transform: scale(1.1);
}

.tab-indicator {
  position: absolute;
  top: 6px;
  left: 6px;
  width: calc(50% - 10px);
  height: calc(100% - 12px);
  background: var(--gradient-primary, linear-gradient(135deg, #667eea 0%, #764ba2 100%));
  border-radius: 8px;
  box-shadow: var(--glow-primary, 0 0 20px rgba(102, 126, 234, 0.4));
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
}

.tab-indicator.tab-register {
  transform: translateX(calc(100% + 8px));
}

/* Forms */
.forms-container {
  margin-bottom: 24px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary, #9ca3af);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-group label svg {
  color: var(--accent-primary, #667eea);
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  padding: 14px 16px;
  background: var(--bg-secondary, rgba(26, 31, 58, 0.6));
  border: 1px solid var(--border-primary, rgba(102, 126, 234, 0.2));
  border-radius: 10px;
  font-size: 15px;
  color: var(--text-primary, #e5e7eb);
  transition: all 0.3s ease;
  outline: none;
}

.input-wrapper input::placeholder {
  color: var(--text-tertiary, #6b7280);
}

.input-wrapper input:focus {
  border-color: var(--border-glow, rgba(102, 126, 234, 0.5));
  box-shadow: var(--glow-primary, 0 0 0 3px rgba(102, 126, 234, 0.1)),
              0 0 20px rgba(102, 126, 234, 0.2);
  background: rgba(26, 31, 58, 0.8);
}

.input-wrapper input:focus + .input-icon {
  color: var(--accent-primary, #667eea);
}

/* Submit Button */
.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 24px;
  background: var(--gradient-primary, linear-gradient(135deg, #667eea 0%, #764ba2 100%));
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 8px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
}

.submit-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.submit-btn:hover:not(:disabled)::before {
  left: 100%;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.5);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-text {
  display: flex;
  align-items: center;
  gap: 10px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error Message */
.error-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-left: 4px solid #ef4444;
  border-radius: 10px;
  color: #fca5a5;
  font-size: 13px;
  font-weight: 500;
  margin-top: 16px;
}

.error-message svg {
  flex-shrink: 0;
  color: #ef4444;
}

.error-fade-enter-active,
.error-fade-leave-active {
  transition: all 0.3s ease;
}

.error-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.error-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Footer */
.card-footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-primary, rgba(102, 126, 234, 0.1));
  display: flex;
  justify-content: center;
}

.footer-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--accent-success, #00ff88);
  letter-spacing: 1px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-success, #00ff88);
  box-shadow: 0 0 10px var(--accent-success, #00ff88);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

/* Responsive */
@media (max-width: 640px) {
  .login-card {
    padding: 32px 24px;
  }

  .logo-icon {
    width: 64px;
    height: 64px;
  }

  .logo-icon svg {
    width: 32px;
    height: 32px;
  }

  .logo-text {
    font-size: 28px;
  }

  .tab-btn {
    font-size: 13px;
    padding: 10px 12px;
  }

  .tab-btn span {
    display: none;
  }

  .form-group label {
    font-size: 12px;
  }

  .input-wrapper input {
    padding: 12px 14px;
    font-size: 14px;
  }

  .submit-btn {
    padding: 14px 20px;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .login-container {
    padding: 16px;
  }

  .login-card {
    padding: 28px 20px;
  }
}
</style>

