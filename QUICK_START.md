# ResearchGO 快速启动指南 🚀

## 最快 3 步启动（Docker）

### 1️⃣ 生成密钥

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

复制输出的密钥。

### 2️⃣ 创建配置文件

在 `backend` 目录创建 `.env` 文件：

```bash
SECRET_KEY=<刚才生成的密钥>
MYSQL_HOST=mysql
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=researchgo123
MYSQL_ROOT_PASSWORD=rootpassword123
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
OPENAI_API_KEY=<你的OpenAI密钥>
```

### 3️⃣ 启动服务

```bash
docker-compose up -d
```

等待 1-2 分钟服务启动完成。

## 🎉 访问应用

打开浏览器访问：http://localhost:5173

**默认账户：**
- 用户名：`admin`
- 密码：`admin123`

⚠️ **首次登录后请立即修改密码！**

## 📦 服务端口

| 服务 | 端口 | 用途 |
|------|------|------|
| 前端 | 5173 | Vue 应用 |
| 后端 | 8000 | FastAPI |
| MySQL | 3306 | 数据库 |
| MinIO API | 9000 | 对象存储 |
| MinIO Console | 9001 | MinIO 管理界面 |
| Milvus | 19530 | 向量数据库 |
| Attu | 9002 | Milvus 管理界面 |

## 🔍 检查服务状态

```bash
# 查看所有容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f mysql
docker-compose logs -f backend
```

## 🛑 停止服务

```bash
# 停止服务（保留数据）
docker-compose stop

# 停止并删除容器（保留数据卷）
docker-compose down

# 完全清理（包括数据）
docker-compose down -v
```

## 🔄 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart mysql
```

## 📝 常见问题

### Q1: 端口被占用怎么办？

修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "5174:5173"  # 改为 5174
```

### Q2: 数据库连接失败？

1. 等待 MySQL 完全启动（约 30 秒）
2. 检查 `.env` 配置是否正确
3. 查看日志：`docker-compose logs mysql`

### Q3: 如何修改密码？

登录后：
1. 点击侧边栏底部的用户头像
2. 选择"退出登录"
3. 使用 API 文档（http://localhost:8000/docs）调用 `/api/auth/me` 的 PUT 方法

## 📚 更多文档

- [完整功能说明](./LOGIN_FEATURE_README.md)
- [详细使用文档](./docs/AUTH_SETUP.md)
- [环境配置指南](./ENV_SETUP_GUIDE.md)
- [API 文档](http://localhost:8000/docs)

## 💡 提示

- 首次启动会自动创建数据库表
- 系统自动创建默认管理员账户
- 所有数据持久化在 Docker 卷中
- Token 默认 7 天有效期

祝使用愉快！🎊

