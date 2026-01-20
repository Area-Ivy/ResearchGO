# 登录认证功能使用指南

## 功能概述

ResearchGO 已集成完整的用户认证系统，包括：

- 用户注册和登录
- JWT Token 认证
- 密码加密存储（bcrypt）
- 路由守卫保护
- MySQL 数据库存储用户信息
- Docker 一键部署

## 快速开始

### 1. 环境配置

#### 复制环境变量文件

```bash
# 根目录
cp .env.example .env

# 后端目录
cp backend/.env.example backend/.env
```

#### 配置必要的环境变量

编辑 `.env` 文件，至少需要配置以下项：

```bash
# JWT密钥（重要！请生成强密钥）
SECRET_KEY=your-secret-key-change-this-in-production

# 数据库密码（建议修改默认密码）
MYSQL_ROOT_PASSWORD=your-root-password
MYSQL_PASSWORD=your-user-password

# OpenAI API Key
OPENAI_API_KEY=your-openai-api-key
```

#### 生成强密钥

使用 Python 生成安全的密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

将生成的密钥填入 `SECRET_KEY`。

### 2. Docker 部署（推荐）

#### 启动所有服务

```bash
docker-compose up -d
```

这将启动：
- MySQL 数据库（端口 3306）
- MinIO 对象存储（端口 9000, 9001）
- Milvus 向量数据库（端口 19530）
- etcd（Milvus 依赖）
- Attu（Milvus 管理界面，端口 9002）

#### 检查服务状态

```bash
docker-compose ps
```

#### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f mysql
```

### 3. 本地开发部署

#### 安装 MySQL

确保本地安装了 MySQL 8.0+，并创建数据库：

```sql
CREATE DATABASE researchgo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'researchgo_user'@'localhost' IDENTIFIED BY 'researchgo123';
GRANT ALL PRIVILEGES ON researchgo.* TO 'researchgo_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 安装后端依赖

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

#### 启动后端服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 安装前端依赖并启动

```bash
cd frontend
npm install
npm run dev
```

## 功能说明

### 后端 API

#### 用户注册

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

响应：

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2024-01-20T10:00:00"
  }
}
```

#### 用户登录

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

支持使用用户名或邮箱登录。

#### 获取当前用户信息

```http
GET /api/auth/me
Authorization: Bearer <token>
```

#### 更新用户信息

```http
PUT /api/auth/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "password": "newpassword123"
}
```

#### 用户登出

```http
POST /api/auth/logout
Authorization: Bearer <token>
```

### 前端页面

#### 登录页面

访问 `http://localhost:5173/login` 查看登录页面。

特性：
- 美观的渐变背景设计
- 登录/注册切换标签
- 表单验证
- 错误提示
- 加载状态

#### 路由守卫

所有需要认证的页面都会自动检查登录状态：

- 未登录访问保护页面 → 重定向到登录页
- 已登录访问登录页 → 重定向到首页
- Token 过期 → 自动清除并重定向到登录页

### 数据库表结构

#### users 表

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);
```

### 默认管理员账户

系统会自动创建一个默认管理员账户：

- 用户名：`admin`
- 邮箱：`admin@researchgo.com`
- 密码：`admin123`

**重要：** 首次登录后请立即修改密码！

## 安全建议

### 生产环境部署

1. **修改所有默认密码**
   - MySQL root 密码
   - MySQL 用户密码
   - MinIO 访问密钥
   - 管理员账户密码

2. **使用强密钥**
   ```bash
   # 生成 32 字节的安全密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **配置 HTTPS**
   - 使用 Nginx 反向代理
   - 配置 SSL 证书（Let's Encrypt）

4. **限制 CORS**
   ```bash
   # 只允许特定域名访问
   ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

5. **配置防火墙**
   - 只开放必要端口（80, 443）
   - 限制数据库访问（只允许本地连接）

6. **定期备份**
   ```bash
   # 备份 MySQL 数据
   docker exec researchgo-mysql mysqldump -u root -p researchgo > backup.sql
   ```

## 故障排除

### 数据库连接失败

检查：
1. MySQL 服务是否启动
2. 数据库配置是否正确（用户名、密码、主机）
3. 数据库是否已创建

```bash
# 查看 MySQL 日志
docker-compose logs mysql
```

### Token 验证失败

可能原因：
1. SECRET_KEY 不一致
2. Token 已过期
3. Token 格式错误

解决方案：重新登录获取新 Token。

### 无法访问登录页

检查：
1. 前端服务是否启动
2. 路由配置是否正确
3. 浏览器控制台是否有错误

### Docker 容器无法启动

```bash
# 查看容器日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 完全重建
docker-compose down
docker-compose up -d --build
```

## API 测试

使用 curl 测试 API：

```bash
# 注册用户
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# 获取用户信息（替换 <token>）
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

## 技术栈

### 后端
- FastAPI - Web 框架
- SQLAlchemy - ORM
- PyMySQL - MySQL 驱动
- Passlib + Bcrypt - 密码加密
- python-jose - JWT 处理
- Pydantic - 数据验证

### 前端
- Vue 3 - UI 框架
- Vue Router - 路由管理
- Axios - HTTP 客户端

### 数据库
- MySQL 8.0 - 用户数据存储

## 后续开发

可以基于此认证系统继续开发：

1. **用户权限管理**
   - 角色系统（admin, user, guest）
   - 细粒度权限控制

2. **社交登录**
   - Google OAuth
   - GitHub OAuth

3. **密码重置**
   - 邮件验证
   - 重置链接

4. **用户资料**
   - 头像上传
   - 个人信息管理

5. **操作日志**
   - 登录历史
   - 操作审计

## 相关文档

- [API 文档](http://localhost:8000/docs) - FastAPI 自动生成的 API 文档
- [MySQL 配置](./MYSQL_SETUP.md)
- [Docker 部署](./DOCKER_DEPLOYMENT.md)

## 支持

如有问题，请查看：
- GitHub Issues
- 项目文档
- API 文档

---

更新时间：2026-01-20

