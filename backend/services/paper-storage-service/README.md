# 论文存储服务 (Paper Storage Service)

独立的论文存储微服务，负责论文上传、下载和管理。

## 功能

- 论文上传（PDF到MinIO）
- 论文列表查询
- 论文下载
- 论文删除
- 论文元数据管理（MySQL）

## 快速启动

### 1. 安装依赖

```bash
cd backend/services/paper-storage-service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `backend/services/paper-storage-service` 目录创建 `.env` 文件：

```env
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=researchgo123

MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=research-papers
```

### 3. 启动服务

```bash
python run.py
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

```

服务将在 http://localhost:8003 运行

## API端点

- `POST /api/papers/upload` - 上传论文
- `GET /api/papers/list` - 获取论文列表
- `GET /api/papers/download/{object_name}` - 下载论文
- `DELETE /api/papers/delete/{object_name}` - 删除论文
- `GET /api/papers/health` - 健康检查

## API文档

启动后访问：http://localhost:8003/docs

## 依赖服务

- MySQL - 存储论文元数据
- MinIO - 存储PDF文件
- 认证服务 (8001) - Token验证

