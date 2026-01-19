# 环境变量配置说明

## 创建 .env 文件

在项目根目录创建 `.env` 文件，添加以下配置：

```bash
# MinIO 对象存储配置
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_ENDPOINT=localhost:9000
MINIO_BUCKET_NAME=researchgo

# Milvus 向量数据库配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=research_papers

# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 后端服务配置
BACKEND_PORT=8080
BACKEND_HOST=0.0.0.0

# 前端服务配置
FRONTEND_PORT=5173
```

## 配置说明

### MinIO 配置
- `MINIO_ROOT_USER`: MinIO 管理员用户名
- `MINIO_ROOT_PASSWORD`: MinIO 管理员密码
- `MINIO_ENDPOINT`: MinIO 服务地址
- `MINIO_BUCKET_NAME`: 存储桶名称

### Milvus 配置
- `MILVUS_HOST`: Milvus 服务主机地址
- `MILVUS_PORT`: Milvus 服务端口（默认 19530）
- `MILVUS_COLLECTION`: 默认集合名称

### OpenAI 配置
- `OPENAI_API_KEY`: OpenAI API 密钥
- `OPENAI_BASE_URL`: OpenAI API 基础 URL

### 服务配置
- `BACKEND_PORT`: 后端服务端口
- `BACKEND_HOST`: 后端服务监听地址
- `FRONTEND_PORT`: 前端服务端口

## 安全建议

1. **不要将 .env 文件提交到版本控制系统**
2. **使用强密码**：修改默认的 MinIO 用户名和密码
3. **保护 API 密钥**：妥善保管 OpenAI API Key
4. **生产环境**：使用环境变量或密钥管理服务

