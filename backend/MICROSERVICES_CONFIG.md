# 微服务配置说明

## 环境变量配置

在 `backend/.env` 文件中添加以下配置：

```env
# 认证服务地址
AUTH_SERVICE_URL=http://localhost:8001
```

## 服务端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| 认证服务 (auth-service) | 8001 | 用户注册、登录、Token验证 |
| 单体服务 (原backend) | 8000 | 其他功能（逐步迁移中） |

## 当前迁移状态

### ✅ 已完成
- [x] 认证服务独立部署 (端口 8001)
- [x] 单体服务的对话API已接入认证服务
- [x] 单体服务移除了认证路由

### 🔄 待迁移
- [ ] 其他API接入认证服务（papers, chat, mindmap, analysis）
- [ ] 论文服务拆分
- [ ] 向量服务拆分
- [ ] 对话服务拆分
- [ ] 聊天服务拆分
- [ ] 思维导图服务拆分
- [ ] 分析服务拆分

## 测试步骤

### 1. 启动认证服务
```bash
cd backend/services/auth-service
.venv\Scripts\activate
python run.py
```

### 2. 启动单体服务
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 测试认证流程

#### 测试认证服务 (端口 8001)
```bash
# 注册用户
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "test123456"}'

# 登录获取Token
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123456"}'
```

#### 测试单体服务调用认证服务 (端口 8000)
```bash
# 使用获取的Token创建对话
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"title": "测试对话"}'
```

### 4. 前端配置

修改 `frontend/src/api/auth.js`，将认证API指向认证服务：

```javascript
// 原来
const API_BASE_URL = 'http://localhost:8000/api/auth'

// 修改为
const AUTH_SERVICE_URL = 'http://localhost:8001/api/auth'
```

## 验证成功标准

✅ 前端能通过认证服务（8001）完成登录
✅ 前端能通过单体服务（8000）访问对话API
✅ 对话API能正确验证认证服务颁发的Token
✅ 单体服务不再提供 `/api/auth/*` 路由

