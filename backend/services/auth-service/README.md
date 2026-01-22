# 认证服务 (Auth Service)

独立的用户认证微服务，负责用户注册、登录和Token验证。

## 功能

- 用户注册
- 用户登录
- Token验证
- 用户信息管理
- 为其他微服务提供身份验证

## 快速启动

### 1. 安装依赖

```bash
cd backend/services/auth-service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `backend/services/auth-service` 目录创建 `.env` 文件：

```env
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=researchgo123
```

### 3. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

服务将在 http://localhost:8001 运行

## API端点

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `PUT /api/auth/me` - 更新用户信息
- `POST /api/auth/verify` - 验证Token（供其他服务调用）
- `POST /api/auth/logout` - 用户登出

## API文档

启动后访问：http://localhost:8001/docs

