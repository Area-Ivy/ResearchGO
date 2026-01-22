# Chat Service (AI 聊天服务)

基于 OpenAI 的 AI 聊天微服务，提供流式和非流式对话功能。

## 服务信息

- **端口**: 8006
- **API 前缀**: `/api/chat`

## 快速启动

```bash
# 1. 进入服务目录
cd backend/services/chat-service

# 2. 创建虚拟环境（可选）
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量（创建 .env 文件）
# 参考下方环境变量配置

# 5. 启动服务
python run.py
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

## 环境变量配置

在服务目录下创建 `.env` 文件：

```env
# OpenAI 配置（必需）
OPENAI_API_KEY=your-openai-api-key

# 可选配置
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

## API 端点

### 健康检查
```
GET /api/chat/health
```

### 发送消息
```
POST /api/chat/message
Content-Type: application/json

{
  "message": "Hello, how are you?",
  "stream": true,
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ],
  "model": "gpt-4o",          // 可选，默认使用环境变量配置
  "temperature": 0.7,         // 可选，默认 0.7
  "max_tokens": 2000          // 可选，默认 2000
}
```

**流式响应 (stream: true)**:
返回 Server-Sent Events (SSE)：
```
event: message
data: {"content": "Hello"}

event: message
data: {"content": "!"}

event: done
data: {"status": "complete"}
```

**非流式响应 (stream: false)**:
```json
{
  "message": "Hello! I'm doing well, thank you for asking.",
  "role": "assistant",
  "finish_reason": "stop"
}
```

## 测试服务

```bash
python test_chat_service.py
```

## 目录结构

```
chat-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── chat.py          # API 路由
│   ├── models/
│   │   ├── __init__.py
│   │   └── chat.py          # Pydantic 数据模型
│   └── services/
│       ├── __init__.py
│       └── openai_service.py # OpenAI API 服务
├── requirements.txt
├── run.py
├── test_chat_service.py
└── README.md
```

## 前端集成

更新 `frontend/src/config.js`：

```javascript
export const CHAT_SERVICE_URL = import.meta.env.VITE_CHAT_SERVICE_URL || 'http://localhost:8006'
```

更新 API 端点：

```javascript
export const API_ENDPOINTS = {
  CHAT_MESSAGE: `${CHAT_SERVICE_URL}/api/chat/message`,
  CHAT_HEALTH: `${CHAT_SERVICE_URL}/api/chat/health`
}
```

## 注意事项

1. 需要有效的 OpenAI API Key
2. 支持自定义 OpenAI 兼容 API（通过 OPENAI_BASE_URL）
3. 流式响应使用 SSE (Server-Sent Events)

