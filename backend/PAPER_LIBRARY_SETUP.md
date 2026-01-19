# 文献库功能设置指南

## 一、安装依赖

### 1. 安装 Python 包

在 `backend` 目录下执行：

```bash
cd backend
pip install -r requirements.txt
```

新增的依赖包：
- `minio==7.2.3` - MinIO Python SDK
- `python-multipart==0.0.6` - FastAPI 文件上传支持

## 二、配置环境变量

### 1. 创建或更新 `.env` 文件

在 `backend` 目录下创建 `.env` 文件（如果不存在），添加以下配置：

```env
# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# OpenAlex 配置
CONTACT_EMAIL=your_email@example.com

# 服务器配置
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=http://localhost:5173

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=research-papers
MINIO_SECURE=False
```

**注意：** 确保 MinIO 的配置与 `.env.minio` 文件中的设置一致。

## 三、启动服务

### 1. 确保 MinIO 正在运行

```bash
# 在项目根目录
docker-compose ps
```

如果 MinIO 未运行，启动它：

```bash
docker-compose up -d
```

### 2. 启动后端服务

```bash
cd backend
python run.py
```

或使用启动脚本（Windows）：

```bash
# 在项目根目录
start-backend.bat
```

## 四、验证安装

### 1. 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

您应该看到新增的 API 端点：

- **POST /api/papers/upload** - 上传论文
- **GET /api/papers/list** - 列出所有论文
- **GET /api/papers/download/{object_name}** - 下载论文
- **DELETE /api/papers/delete/{object_name}** - 删除论文
- **GET /api/papers/health** - 健康检查

### 2. 测试健康检查

```bash
curl http://localhost:8000/api/papers/health
```

应该返回：

```json
{
  "status": "healthy",
  "service": "papers",
  "minio": "connected"
}
```

### 3. 测试上传功能

在 Swagger UI (http://localhost:8000/docs) 中：

1. 找到 **POST /api/papers/upload** 端点
2. 点击 "Try it out"
3. 选择一个 PDF 文件
4. 点击 "Execute"

成功响应示例：

```json
{
  "object_name": "20240116_123456_example.pdf",
  "original_name": "example.pdf",
  "size": 1048576,
  "content_type": "application/pdf",
  "upload_time": "2024-01-16T12:34:56.789",
  "message": "File uploaded successfully"
}
```

### 4. 测试列表功能

```bash
curl http://localhost:8000/api/papers/list
```

应该返回已上传的文件列表。

## 五、API 使用说明

### 上传论文

```bash
curl -X POST "http://localhost:8000/api/papers/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/paper.pdf"
```

### 列出所有论文

```bash
curl http://localhost:8000/api/papers/list
```

### 下载论文

```bash
curl -O "http://localhost:8000/api/papers/download/20240116_123456_example.pdf"
```

### 删除论文

```bash
curl -X DELETE "http://localhost:8000/api/papers/delete/20240116_123456_example.pdf"
```

## 六、文件存储说明

### 存储位置

- **MinIO 容器内**：`/data` 目录
- **宿主机映射**：`项目根目录/minio_data`

### 文件命名规则

上传的文件会自动添加时间戳前缀，格式为：

```
YYYYMMDD_HHMMSS_原始文件名.pdf
```

例如：`20240116_143022_research_paper.pdf`

这样可以避免文件名冲突，同时保留原始文件名。

### 元数据

每个文件都包含以下元数据：

- `original_name`: 原始文件名
- `upload_time`: 上传时间（ISO 8601 格式）
- `content_type`: 文件类型（通常为 application/pdf）

## 七、故障排查

### 问题 1：MinIO 连接失败

**错误信息：** "minio: disconnected"

**解决方案：**

1. 检查 MinIO 是否运行：
   ```bash
   docker-compose ps
   ```

2. 检查 `.env` 文件中的 MinIO 配置

3. 重启 MinIO：
   ```bash
   docker-compose restart minio
   ```

### 问题 2：上传失败

**错误信息：** "Failed to upload file"

**可能原因：**

1. **文件类型不支持**：只支持 PDF 文件
2. **MinIO 存储桶不存在**：
   - 访问 http://localhost:9001
   - 登录并创建 `research-papers` 桶
3. **MinIO 权限问题**：检查访问密钥是否正确

### 问题 3：导入错误

**错误信息：** "Import 'minio' could not be resolved"

**解决方案：**

```bash
cd backend
pip install minio==7.2.3 python-multipart==0.0.6
```

### 问题 4：文件下载失败

**错误信息：** "Paper not found"

**可能原因：**

1. 对象名称错误（需要包含时间戳前缀）
2. 文件已被删除
3. MinIO 连接问题

## 八、安全建议

### 开发环境

- 使用默认的 MinIO 凭证即可
- 仅在本地网络访问

### 生产环境

1. **修改 MinIO 密码**：
   - 编辑 `.env.minio` 和 `backend/.env`
   - 使用强密码

2. **启用 HTTPS**：
   - 配置反向代理（Nginx）
   - 设置 `MINIO_SECURE=True`

3. **文件大小限制**：
   - 在 Nginx 中配置 `client_max_body_size`
   - 在 FastAPI 中添加文件大小验证

4. **访问控制**：
   - 添加用户认证
   - 实现权限管理

## 九、下一步

后端 API 完成后，可以继续：

1. **前端开发**：创建文献库页面
2. **功能增强**：
   - 添加文件预览
   - 实现全文搜索
   - 添加标签和分类
   - 支持批量操作

## 十、相关文档

- [MinIO 部署指南](../MINIO_SETUP.md)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/minio-py.html)

