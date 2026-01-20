# 环境配置指南

## 快速配置

### 1. 后端环境变量

在 `backend` 目录下创建 `.env` 文件：

```bash
# OpenAI API
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o
CONTACT_EMAIL=your-email@example.com

# MySQL数据库（本地开发）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=researchgo123

# MySQL数据库（Docker环境，取消注释并注释上面的配置）
# MYSQL_HOST=mysql
# MYSQL_PORT=3306
# MYSQL_DATABASE=researchgo
# MYSQL_USER=researchgo_user
# MYSQL_PASSWORD=researchgo123

# JWT认证（请生成强密钥）
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# MinIO（本地开发）
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=research-papers

# MinIO（Docker环境）
# MINIO_ENDPOINT=minio:9000

# CORS
ALLOWED_ORIGINS=*
```

### 2. 生成安全密钥

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

将输出的密钥复制到 `SECRET_KEY`。

### 3. Docker 环境变量

创建项目根目录的 `.env` 文件（用于 docker-compose）：

```bash
# MySQL配置
MYSQL_ROOT_PASSWORD=rootpassword123
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=researchgo123

# MinIO配置
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
```

## 部署说明

### Docker 部署

1. 确保已安装 Docker 和 Docker Compose
2. 配置环境变量文件
3. 启动服务：

```bash
docker-compose up -d
```

4. 检查服务状态：

```bash
docker-compose ps
```

### 本地开发

1. 安装 MySQL 8.0+
2. 创建数据库和用户
3. 配置环境变量
4. 启动后端：

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. 启动前端：

```bash
cd frontend
npm run dev
```

## 默认账户

- 用户名：`admin`
- 密码：`admin123`

**首次登录后请立即修改密码！**

