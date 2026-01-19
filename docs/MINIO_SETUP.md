# MinIO 部署与配置指南

## 一、MinIO 简介

MinIO 是一个高性能的对象存储服务，兼容 Amazon S3 API。本项目使用 MinIO 存储用户上传的 PDF 论文文件。

## 二、前置要求

- Docker Desktop（Windows/Mac）或 Docker Engine（Linux）
- Docker Compose v2.0+

### 验证 Docker 安装

```bash
docker --version
docker-compose --version
```

## 三、部署步骤

### 3.1 创建环境变量文件

在项目根目录创建 `.env.minio` 文件（如果不存在的话）：

**Windows PowerShell:**
```powershell
@"
# MinIO 访问凭证
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# MinIO 连接配置（用于后端应用）
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=research-papers
MINIO_SECURE=false
"@ | Out-File -FilePath .env.minio -Encoding UTF8
```

**Windows CMD / Mac / Linux:**
```bash
cat > .env.minio << 'EOF'
# MinIO 访问凭证
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# MinIO 连接配置（用于后端应用）
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=research-papers
MINIO_SECURE=false
EOF
```

或者直接创建文本文件，复制以下内容：
```
# MinIO 访问凭证
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# MinIO 连接配置（用于后端应用）
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=research-papers
MINIO_SECURE=false
```

### 3.2 启动 MinIO 服务

在项目根目录执行：

```bash
docker-compose up -d
```

**参数说明：**
- `-d`: 后台运行
- 首次启动会自动下载 MinIO 镜像（约 100MB）

### 3.3 验证服务状态

```bash
docker-compose ps
```

应该看到 `researchgo-minio` 容器状态为 `Up`。

### 3.4 查看日志

```bash
docker-compose logs -f minio
```

按 `Ctrl+C` 退出日志查看。

## 四、访问 MinIO 控制台

### 4.1 打开浏览器

访问：`http://localhost:9001`

### 4.2 登录

- **用户名**: `minioadmin`
- **密码**: `minioadmin123`

### 4.3 创建存储桶（Bucket）

1. 点击左侧菜单 **"Buckets"**
2. 点击右上角 **"Create Bucket"**
3. 输入桶名称：`research-papers`
4. 点击 **"Create Bucket"**

### 4.4 设置访问策略（可选）

如果需要公开访问部分文件：

1. 进入 `research-papers` 桶
2. 点击 **"Access"** 标签
3. 选择 **"Public"** 或自定义策略

**注意：** 开发环境建议保持默认（私有），通过后端 API 控制访问。

## 五、MinIO 常用命令

### 启动服务
```bash
docker-compose up -d
```

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

### 查看日志
```bash
docker-compose logs -f minio
```

### 完全删除（包括数据）
```bash
docker-compose down -v
rm -rf minio_data
```

**警告：** 此操作会删除所有上传的文件！

## 六、数据存储位置

- **Windows**: `D:\code\ResearchGO\minio_data`
- **Mac/Linux**: `项目根目录/minio_data`

所有上传的文件都存储在此目录，可以直接备份。

## 七、端口说明

| 端口 | 用途 | 访问地址 |
|------|------|----------|
| 9000 | MinIO API | http://localhost:9000 |
| 9001 | MinIO Console | http://localhost:9001 |

**端口冲突：** 如果端口被占用，修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "9002:9000"  # 将 API 端口改为 9002
  - "9003:9001"  # 将控制台改为 9003
```

## 八、安全建议

### 开发环境
- 使用默认密码即可
- 仅本地访问

### 生产环境
1. **修改密码**：编辑 `.env.minio` 文件
   ```env
   MINIO_ROOT_USER=your_admin_username
   MINIO_ROOT_PASSWORD=your_strong_password_here
   ```

2. **启用 HTTPS**：配置反向代理（Nginx/Caddy）

3. **访问控制**：使用 IAM 策略限制权限

## 九、故障排查

### 问题 1：容器无法启动
```bash
# 查看详细错误
docker-compose logs minio

# 常见原因：端口被占用
# 解决：修改 docker-compose.yml 中的端口
```

### 问题 2：无法访问控制台
```bash
# 检查容器状态
docker ps | grep minio

# 检查端口监听
netstat -ano | findstr 9001  # Windows
lsof -i :9001                # Mac/Linux

# 尝试重启
docker-compose restart minio
```

### 问题 3：数据丢失
- 确认 `minio_data` 目录存在
- 检查 Docker 卷挂载：`docker volume ls`

## 十、下一步

MinIO 部署完成后，可以进行：

1. **后端集成**：安装 `minio` Python 包，实现上传/下载 API
2. **前端开发**：创建文件上传界面和论文列表
3. **测试验证**：手动上传文件测试

## 十一、参考资源

- [MinIO 官方文档](https://min.io/docs/minio/linux/index.html)
- [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/minio-py.html)
- [Docker Compose 文档](https://docs.docker.com/compose/)

