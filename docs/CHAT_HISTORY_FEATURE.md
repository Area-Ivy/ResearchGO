# Chat历史对话功能实现指南

## 📋 功能概述

为Chat页面添加完整的历史对话功能，包括：
- ✅ 创建新对话会话
- ✅ 保存对话消息到数据库
- ✅ 查看历史对话列表
- ✅ 切换和加载历史对话
- ✅ 重命名对话标题
- ✅ 删除历史对话

## 🗄️ 数据库设计

### 表结构

#### conversations（对话会话表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| user_id | INT | 用户ID（外键） |
| title | VARCHAR(255) | 对话标题 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| is_deleted | BOOLEAN | 软删除标记 |

#### messages（消息表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| conversation_id | INT | 会话ID（外键） |
| role | VARCHAR(20) | 角色（user/assistant） |
| content | TEXT | 消息内容 |
| created_at | TIMESTAMP | 创建时间 |

## 🚀 部署步骤

### 1. 创建数据库表

运行迁移脚本：

```bash
# 方式1：直接在MySQL容器中执行
docker exec -i researchgo-mysql mysql -u root -prootpassword123 researchgo < backend/migrations/002_create_conversations.sql

# 方式2：进入容器后执行
docker exec -it researchgo-mysql mysql -u root -prootpassword123 researchgo
```

然后在MySQL中运行：

```sql
-- 创建对话会话表
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    INDEX idx_user_id (user_id),
    INDEX idx_updated_at (updated_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建消息表
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

验证表已创建：
```sql
SHOW TABLES;
DESCRIBE conversations;
DESCRIBE messages;
```

### 2. 重启后端服务

后端代码已自动包含新的路由，只需重启：

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 验证API

访问 API 文档：http://localhost:8000/docs

查找 "对话管理" 标签下的接口：
- `POST /api/conversations` - 创建对话
- `GET /api/conversations` - 获取对话列表
- `GET /api/conversations/{id}` - 获取对话详情
- `PUT /api/conversations/{id}` - 更新对话
- `DELETE /api/conversations/{id}` - 删除对话
- `POST /api/conversations/{id}/messages` - 添加消息
- `GET /api/conversations/{id}/messages` - 获取消息列表

## 📡 API使用示例

### 创建新对话

```javascript
import { createConversation } from '@/api/conversations'

const conversation = await createConversation('关于深度学习的讨论')
// 返回: { id: 1, user_id: 1, title: '关于深度学习的讨论', ... }
```

### 获取对话列表

```javascript
import { getConversations } from '@/api/conversations'

const { total, conversations } = await getConversations(0, 50)
// conversations: [{ id, title, message_count, updated_at, ... }]
```

### 添加消息到对话

```javascript
import { addMessage } from '@/api/conversations'

// 添加用户消息
await addMessage(conversationId, 'user', '什么是Transformer?')

// 添加AI回复
await addMessage(conversationId, 'assistant', 'Transformer是...')
```

### 加载历史对话

```javascript
import { getConversation } from '@/api/conversations'

const conversation = await getConversation(conversationId)
// 返回: { id, title, messages: [{role, content, created_at}, ...] }
```

### 删除对话

```javascript
import { deleteConversation } from '@/api/conversations'

await deleteConversation(conversationId)
```

## 🎨 前端集成示例

### Chat.vue 组件修改要点

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { 
  createConversation, 
  getConversations, 
  getConversation,
  addMessage,
  deleteConversation 
} from '@/api/conversations'

// 状态管理
const conversations = ref([])
const currentConversation = ref(null)
const messages = ref([])

// 加载对话列表
const loadConversations = async () => {
  const data = await getConversations()
  conversations.value = data.conversations
}

// 创建新对话
const createNewChat = async () => {
  const conv = await createConversation('新对话')
  currentConversation.value = conv
  messages.value = []
  await loadConversations()
}

// 切换对话
const switchConversation = async (conversationId) => {
  const conv = await getConversation(conversationId)
  currentConversation.value = conv
  messages.value = conv.messages
}

// 发送消息
const sendMessage = async (userMessage) => {
  // 如果没有当前对话，创建新对话
  if (!currentConversation.value) {
    await createNewChat()
  }

  // 保存用户消息
  await addMessage(currentConversation.value.id, 'user', userMessage)
  
  // 调用AI获取回复...
  const aiResponse = await getAIResponse(userMessage)
  
  // 保存AI回复
  await addMessage(currentConversation.value.id, 'assistant', aiResponse)
  
  // 刷新消息列表
  await switchConversation(currentConversation.value.id)
}

// 删除对话
const deleteChat = async (conversationId) => {
  await deleteConversation(conversationId)
  if (currentConversation.value?.id === conversationId) {
    currentConversation.value = null
    messages.value = []
  }
  await loadConversations()
}

onMounted(() => {
  loadConversations()
})
</script>
```

### 界面布局建议

```vue
<template>
  <div class="chat-container">
    <!-- 左侧：历史对话列表 -->
    <aside class="chat-sidebar">
      <button @click="createNewChat" class="new-chat-btn">
        + 新对话
      </button>
      
      <div class="conversation-list">
        <div 
          v-for="conv in conversations" 
          :key="conv.id"
          :class="['conversation-item', { active: currentConversation?.id === conv.id }]"
          @click="switchConversation(conv.id)"
        >
          <div class="conv-title">{{ conv.title }}</div>
          <div class="conv-meta">
            <span>{{ conv.message_count }} 条消息</span>
            <button @click.stop="deleteChat(conv.id)">删除</button>
          </div>
        </div>
      </div>
    </aside>

    <!-- 右侧：当前对话 -->
    <main class="chat-main">
      <div class="messages">
        <div v-for="msg in messages" :key="msg.id" :class="`message-${msg.role}`">
          {{ msg.content }}
        </div>
      </div>
      
      <div class="input-area">
        <input v-model="inputMessage" @keyup.enter="sendMessage(inputMessage)" />
        <button @click="sendMessage(inputMessage)">发送</button>
      </div>
    </main>
  </div>
</template>
```

## 🎯 实现流程

### 用户第一次发送消息
1. 检测当前没有活动对话
2. 自动创建新对话（标题使用用户第一句话的前20字）
3. 保存用户消息到数据库
4. 调用AI接口获取回复
5. 保存AI回复到数据库

### 用户切换历史对话
1. 点击侧边栏的历史对话项
2. 调用API加载该对话的所有消息
3. 显示在聊天界面中

### 用户继续历史对话
1. 在已有对话中发送新消息
2. 保存到当前对话的messages表中
3. 更新对话的updated_at时间

## 🔧 高级功能

### 1. 自动生成对话标题

```javascript
const generateTitle = (firstMessage) => {
  // 使用用户第一句话的前30个字符作为标题
  return firstMessage.substring(0, 30) + (firstMessage.length > 30 ? '...' : '')
}

// 或者使用AI生成更好的标题
const generateAITitle = async (messages) => {
  const response = await openai.chat({
    messages: [
      { role: 'system', content: '请为以下对话生成一个简短的标题（不超过20字）' },
      { role: 'user', content: messages.map(m => m.content).join('\n') }
    ]
  })
  return response
}
```

### 2. 搜索历史对话

```javascript
const searchConversations = async (keyword) => {
  // 在标题和消息内容中搜索
  return conversations.value.filter(conv => 
    conv.title.includes(keyword)
  )
}
```

### 3. 导出对话

```javascript
const exportConversation = (conversation) => {
  const text = conversation.messages.map(msg => 
    `${msg.role === 'user' ? '你' : 'AI'}: ${msg.content}`
  ).join('\n\n')
  
  const blob = new Blob([text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${conversation.title}.txt`
  a.click()
}
```

### 4. 对话分享

```javascript
// 生成分享链接（需要实现公开分享功能）
const shareConversation = async (conversationId) => {
  const shareToken = await createShareToken(conversationId)
  return `${window.location.origin}/shared/${shareToken}`
}
```

## 🎨 UI/UX 建议

### 布局
- **侧边栏宽度**: 260px-300px
- **可折叠**: 移动端自动隐藏，点击按钮显示
- **固定按钮**: "新对话" 按钮固定在顶部

### 交互
- **当前对话高亮**: 使用渐变背景色
- **悬停效果**: 显示删除、重命名按钮
- **拖动排序**: 支持对话列表拖动排序
- **无限滚动**: 历史对话列表支持分页加载

### 样式参考

```css
.chat-sidebar {
  width: 280px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
}

.new-chat-btn {
  margin: 16px;
  padding: 12px;
  background: var(--gradient-primary);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.conversation-item {
  padding: 12px 16px;
  margin: 4px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.conversation-item:hover {
  background: rgba(102, 126, 234, 0.1);
}

.conversation-item.active {
  background: var(--gradient-primary);
  color: white;
}
```

## 🐛 常见问题

### Q1: 消息没有保存到数据库？
- 检查是否已创建对话会话
- 确认API调用是否成功
- 查看后端日志

### Q2: 切换对话后消息没有加载？
- 确认 `getConversation` API 返回了messages字段
- 检查messages数组是否正确赋值

### Q3: 删除对话后UI没有更新？
- 确保删除后调用了 `loadConversations()`
- 检查是否清除了当前对话状态

## 📊 性能优化

### 1. 消息分页加载
```javascript
// 只加载最近50条消息
const loadMessages = async (conversationId, limit = 50) => {
  const messages = await getMessages(conversationId)
  return messages.slice(-limit)
}
```

### 2. 虚拟滚动
对于超长对话，使用虚拟滚动库如 `vue-virtual-scroller`

### 3. 本地缓存
```javascript
// 缓存对话列表，减少API调用
const cachedConversations = ref(null)
const cacheTime = 60000 // 1分钟

const loadConversations = async (forceRefresh = false) => {
  if (!forceRefresh && cachedConversations.value) {
    return cachedConversations.value
  }
  
  const data = await getConversations()
  cachedConversations.value = data
  return data
}
```

## ✅ 测试检查清单

- [ ] 创建新对话
- [ ] 发送消息并保存
- [ ] 切换历史对话
- [ ] 重命名对话标题
- [ ] 删除对话
- [ ] 加载更多历史对话
- [ ] 搜索对话
- [ ] 移动端响应式布局
- [ ] 退出登录后对话是否正确隔离

## 🚀 下一步增强

1. **对话标签**: 给对话添加标签分类
2. **对话归档**: 归档不常用的对话
3. **多模态支持**: 支持图片、文件等
4. **协作功能**: 分享对话给其他用户
5. **对话统计**: 显示总消息数、最活跃对话等

---

**实现时间**: 2026-01-20  
**版本**: 1.0.0  
**状态**: ✅ 后端API已完成，前端待集成

