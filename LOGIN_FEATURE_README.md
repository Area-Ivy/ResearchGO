# ResearchGO 登录功能实现完成 ✅

## 🎉 功能概述

已成功为 ResearchGO 系统实现完整的用户认证功能，包括：

### ✨ 核心特性

- ✅ 用户注册和登录
- ✅ JWT Token 认证机制
- ✅ 密码加密存储（bcrypt + salt）
- ✅ 前端路由守卫保护
- ✅ MySQL 数据库集成
- ✅ Docker 一键部署
- ✅ 美观的登录界面
- ✅ 用户信息显示
- ✅ 安全的登出功能

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

1. **配置环境变量**

在项目根目录创建 `.env` 文件（可参考本文档底部示例）：

```bash
# 最小配置
SECRET_KEY=<生成的强密钥>
MYSQL_ROOT_PASSWORD=your-password
MYSQL_PASSWORD=your-password
```

生成密钥：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **启动服务**

```bash
docker-compose up -d
```

3. **访问应用**

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- MinIO 控制台：http://localhost:9001
- Attu (Milvus UI)：http://localhost:9002

4. **使用默认账户登录**

- 用户名：`admin`
- 密码：`admin123`

**⚠️ 重要：首次登录后请立即修改密码！**

### 方式二：本地开发

#### 1. 设置数据库

```sql
CREATE DATABASE researchgo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'researchgo_user'@'localhost' IDENTIFIED BY 'researchgo123';
GRANT ALL PRIVILEGES ON researchgo.* TO 'researchgo_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 2. 配置后端

在 `backend` 目录创建 `.env` 文件：

```bash
# 数据库
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=researchgo123

# JWT
SECRET_KEY=<生成的强密钥>
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# OpenAI (可选)
OPENAI_API_KEY=your-key
```

#### 3. 安装依赖并启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

## 📁 项目结构

### 后端新增文件

```
backend/
├── app/
│   ├── database.py              # 数据库配置和连接
│   ├── models/
│   │   └── user.py             # 用户数据模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py             # Pydantic 验证模型
│   ├── api/
│   │   └── auth.py             # 认证 API 路由
│   └── utils/
│       ├── security.py          # 密码加密和 JWT 处理
│       └── auth.py              # 认证依赖和中间件
└── init.sql                     # 数据库初始化脚本
```

### 前端新增文件

```
frontend/
└── src/
    ├── views/
    │   └── Login.vue            # 登录/注册页面
    └── api/
        └── auth.js              # 认证相关 API
```

### 配置文件

```
.
├── docker-compose.yml           # 添加了 MySQL 服务
├── docs/
│   └── AUTH_SETUP.md           # 详细使用文档
├── ENV_SETUP_GUIDE.md          # 环境配置指南
└── LOGIN_FEATURE_README.md     # 本文件
```

## 🔐 安全特性

### 密码安全
- 使用 bcrypt 算法加密
- 自动添加随机 salt
- 12 轮哈希迭代

### Token 安全
- JWT (JSON Web Token)
- HS256 算法签名
- 可配置过期时间（默认 7 天）
- 包含用户 ID 和用户名

### API 安全
- HTTP Bearer 认证
- 自动 Token 验证
- 401 错误自动重定向登录
- 路由级别的权限控制

## 🎨 前端特性

### 登录页面
- 渐变背景设计
- 登录/注册切换标签
- 实时表单验证
- 友好的错误提示
- 加载状态反馈
- 响应式设计

### 路由守卫
- 自动检测登录状态
- 未登录自动重定向
- Token 过期处理
- 会话保持

### 用户界面
- 侧边栏显示用户信息
- 用户菜单（点击头像）
- 安全登出功能
- 登录页面隐藏侧边栏

## 📡 API 接口

### 用户注册
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123"
}
```

### 用户登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "newuser",  // 支持用户名或邮箱
  "password": "password123"
}
```

### 获取当前用户
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### 更新用户信息
```http
PUT /api/auth/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "password": "newpassword"
}
```

### 登出
```http
POST /api/auth/logout
Authorization: Bearer <token>
```

## 🗄️ 数据库表结构

### users 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| username | VARCHAR(50) | 用户名，唯一 |
| email | VARCHAR(100) | 邮箱，唯一 |
| hashed_password | VARCHAR(255) | 加密后的密码 |
| is_active | BOOLEAN | 是否激活 |
| is_superuser | BOOLEAN | 是否超级管理员 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

索引：
- `idx_username` on `username`
- `idx_email` on `email`

## 🔧 技术栈

### 后端
| 技术 | 用途 |
|------|------|
| FastAPI | Web 框架 |
| SQLAlchemy | ORM 数据库操作 |
| PyMySQL | MySQL 驱动 |
| Passlib + Bcrypt | 密码加密 |
| python-jose | JWT Token 处理 |
| Pydantic | 数据验证 |

### 前端
| 技术 | 用途 |
|------|------|
| Vue 3 | UI 框架 |
| Vue Router | 路由管理 |
| Axios | HTTP 客户端 |

### 数据库
| 技术 | 用途 |
|------|------|
| MySQL 8.0 | 关系型数据库 |

### 部署
| 技术 | 用途 |
|------|------|
| Docker | 容器化 |
| Docker Compose | 服务编排 |

## ⚙️ 环境变量说明

### 必需配置

```bash
# JWT 密钥（必须修改！）
SECRET_KEY=your-secret-key-here

# 数据库配置
MYSQL_HOST=localhost
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=your-password
```

### 可选配置

```bash
# Token 过期时间（分钟，默认 10080 = 7天）
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS 设置（生产环境应限制）
ALLOWED_ORIGINS=*

# OpenAI API
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o
```

## 📝 使用示例

### 命令行测试

```bash
# 注册新用户
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# 获取用户信息（需要替换 TOKEN）
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 前端使用

```javascript
import { login, logout, getCurrentUser } from '@/api/auth'

// 登录
const response = await login({
  username: 'testuser',
  password: 'password123'
})
localStorage.setItem('token', response.access_token)

// 获取用户信息
const user = await getCurrentUser()

// 登出
await logout()
```

## 🔍 故障排除

### 问题：数据库连接失败

**症状：** 后端启动报错 "Can't connect to MySQL server"

**解决方案：**
1. 确认 MySQL 服务已启动
2. 检查 `.env` 中的数据库配置
3. 确认数据库和用户已创建
4. 查看 Docker 日志：`docker-compose logs mysql`

### 问题：Token 验证失败

**症状：** API 返回 401 Unauthorized

**解决方案：**
1. 检查 `SECRET_KEY` 是否一致
2. 确认 Token 未过期
3. 清除浏览器 localStorage 并重新登录

### 问题：无法访问登录页

**症状：** 页面空白或 404

**解决方案：**
1. 确认前端服务已启动：`npm run dev`
2. 检查路由配置
3. 查看浏览器控制台错误

### 问题：Docker 容器启动失败

**解决方案：**
```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 完全重建
docker-compose down -v
docker-compose up -d --build
```

## 🛡️ 生产环境建议

### 必做项

1. **修改所有默认密码**
   - MySQL root 密码
   - MySQL 用户密码
   - 管理员账户密码
   - MinIO 访问密钥

2. **使用强密钥**
   ```bash
   # 生成 256 位密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **配置 HTTPS**
   - 使用 Nginx 反向代理
   - 配置 SSL 证书（Let's Encrypt）

4. **限制 CORS**
   ```bash
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

5. **配置防火墙**
   - 只开放 80/443 端口
   - 限制数据库端口访问

### 推荐项

1. **设置更短的 Token 过期时间**
   ```bash
   ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1小时
   ```

2. **启用日志记录**
3. **定期数据库备份**
4. **监控系统资源**
5. **实施 Rate Limiting**

## 📚 相关文档

- [详细使用文档](./docs/AUTH_SETUP.md) - 完整的功能说明和使用指南
- [环境配置指南](./ENV_SETUP_GUIDE.md) - 环境变量配置说明
- [API 文档](http://localhost:8000/docs) - FastAPI 自动生成的交互式文档

## 🎯 后续开发建议

基于现有认证系统，可以继续开发：

### 1. 权限管理
- [ ] 角色系统（Admin, User, Guest）
- [ ] 基于角色的访问控制（RBAC）
- [ ] 细粒度权限管理

### 2. 社交登录
- [ ] Google OAuth 2.0
- [ ] GitHub OAuth
- [ ] 微信登录

### 3. 密码管理
- [ ] 忘记密码功能
- [ ] 邮件验证
- [ ] 密码重置链接
- [ ] 密码强度要求

### 4. 用户资料
- [ ] 头像上传
- [ ] 个人信息管理
- [ ] 偏好设置

### 5. 安全增强
- [ ] 双因素认证（2FA）
- [ ] 登录历史记录
- [ ] IP 白名单
- [ ] 操作审计日志

### 6. Token 刷新
- [ ] Refresh Token 机制
- [ ] 自动续期
- [ ] 多设备管理

## 💡 环境变量配置示例

### 根目录 `.env`（用于 Docker）

```bash
# MySQL
MYSQL_ROOT_PASSWORD=Your-Strong-Root-Password-Here
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=Your-Strong-User-Password-Here

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=Your-Strong-MinIO-Password-Here
```

### `backend/.env`（用于应用）

```bash
# 数据库（Docker 环境）
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=Your-Strong-User-Password-Here

# 数据库（本地开发）
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_DATABASE=researchgo
# MYSQL_USER=researchgo_user
# MYSQL_PASSWORD=Your-Strong-User-Password-Here

# JWT 认证（必须修改！）
SECRET_KEY=Your-Secret-Key-Generated-By-Python
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o
CONTACT_EMAIL=your-email@example.com

# MinIO（Docker 环境）
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=Your-Strong-MinIO-Password-Here
MINIO_BUCKET_NAME=research-papers

# MinIO（本地开发）
# MINIO_ENDPOINT=localhost:9000
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=Your-Strong-MinIO-Password-Here
# MINIO_BUCKET_NAME=research-papers

# CORS
ALLOWED_ORIGINS=*
```

## ✅ 功能清单

- [x] MySQL 数据库集成
- [x] 用户数据模型
- [x] 密码加密（bcrypt）
- [x] JWT Token 生成和验证
- [x] 用户注册 API
- [x] 用户登录 API
- [x] 获取用户信息 API
- [x] 更新用户信息 API
- [x] 登出 API
- [x] 前端登录页面
- [x] 前端路由守卫
- [x] Token 自动管理
- [x] 用户信息显示
- [x] 登出功能
- [x] Docker 部署配置
- [x] 数据库初始化脚本
- [x] 环境变量配置
- [x] 使用文档

## 📞 支持

如有问题或需要帮助，请：
1. 查看 [详细文档](./docs/AUTH_SETUP.md)
2. 访问 [API 文档](http://localhost:8000/docs)
3. 检查 Docker 日志
4. 提交 GitHub Issue

---

**实现时间：** 2026-01-20
**版本：** 1.0.0
**状态：** ✅ 已完成并可用

祝使用愉快！🎉

