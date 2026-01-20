# 修复数据库连接问题

## ✅ 已完成的操作

1. ✅ 已停止并删除旧的MySQL容器
2. ✅ 已删除MySQL数据卷
3. ✅ 已重新启动MySQL容器（正在初始化...）

## 📝 下一步操作

### 1. 等待MySQL初始化（30秒）

等待约30秒让MySQL完全启动并执行初始化脚本。

检查MySQL状态：
```bash
docker-compose logs mysql
```

看到类似 `ready for connections` 的消息说明MySQL已就绪。

### 2. 配置后端环境变量

在 `backend` 目录创建 `.env` 文件，内容如下：

```bash
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=researchgo123

# JWT密钥（重要！请生成新密钥）
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# OpenAI（可选）
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# CORS
ALLOWED_ORIGINS=*
```

### 3. 生成JWT密钥

**重要：** 必须生成一个强密钥！

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

将生成的密钥替换 `.env` 文件中的 `SECRET_KEY`。

### 4. 重启后端服务

停止当前后端服务（Ctrl+C），然后重新启动：

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔍 验证连接

### 检查MySQL状态
```bash
docker-compose ps
```

确保 `researchgo-mysql` 状态为 `healthy` 或 `running`。

### 查看MySQL日志
```bash
docker-compose logs -f mysql
```

应该看到：
- `ready for connections`
- 没有错误信息

### 测试数据库连接

进入MySQL容器：
```bash
docker exec -it researchgo-mysql mysql -u researchgo_user -presearchgo123 researchgo
```

在MySQL提示符下运行：
```sql
SHOW TABLES;
SELECT * FROM users;
```

应该能看到 `users` 表和一个 `admin` 用户。

## 🚀 测试登录

1. 访问：http://localhost:5173/login
2. 使用默认账户：
   - 用户名：`admin`
   - 密码：`admin123`

## ❓ 常见问题

### Q1: 仍然无法连接？

检查 `.env` 文件是否在正确位置（`backend/.env`）。

### Q2: 端口冲突？

如果3306端口被占用，修改 `docker-compose.yml`：
```yaml
ports:
  - "3307:3306"  # 改为3307
```

然后在 `.env` 中：
```bash
MYSQL_PORT=3307
```

### Q3: 密码错误？

确保 `.env` 中的密码与 `docker-compose.yml` 中的一致。

默认密码是：`researchgo123`

### Q4: 完全重置？

```bash
# 停止所有服务
docker-compose down

# 删除所有数据卷
docker volume rm researchgo_mysql_data

# 重新启动
docker-compose up -d
```

## 📊 数据库信息

### 默认配置
- 数据库名：`researchgo`
- 用户名：`researchgo_user`
- 密码：`researchgo123`
- Root密码：`rootpassword123`

### 默认管理员账户
- 用户名：`admin`
- 邮箱：`admin@researchgo.com`
- 密码：`admin123`

⚠️ **生产环境请务必修改所有默认密码！**

## 💡 快速命令

```bash
# 查看所有容器状态
docker-compose ps

# 查看MySQL日志
docker-compose logs -f mysql

# 重启MySQL
docker-compose restart mysql

# 进入MySQL容器
docker exec -it researchgo-mysql bash

# 连接数据库
docker exec -it researchgo-mysql mysql -u root -prootpassword123
```

---

**更新时间：** 2026-01-20
**状态：** MySQL已重新初始化，等待配置后端连接

