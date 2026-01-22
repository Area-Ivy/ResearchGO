# 向量搜索服务 (Vector Search Service)

独立的向量搜索微服务，负责语义搜索和论文问答。

## 功能

- 语义搜索 - 在所有论文中搜索相关内容
- 论文问答 (Paper QA) - 基于特定论文回答问题
- 论文索引 - 将论文内容切分并生成向量索引
- 向量删除 - 删除论文的向量索引

## 技术栈

- **Milvus** - 向量数据库
- **OpenAI** - 文本嵌入和AI回答生成
- **FastAPI** - Web框架

## 快速启动

### 1. 安装依赖

```bash
cd backend\services\vector-search-service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `backend/services/vector-search-service` 目录创建 `.env` 文件：

```env
SECRET_KEY=your-secret-key-here
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=research_papers

OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### 3. 启动服务

```bash
python run.py
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload

```

服务将在 http://localhost:8004 运行

## API端点

### 语义搜索
- `POST /api/vector/search` - 语义搜索

### 论文问答
- `POST /api/vector/qa` - 基于论文回答问题

### 索引管理
- `POST /api/vector/index` - 索引论文
- `DELETE /api/vector/delete/{paper_id}` - 删除论文索引

### 统计和健康检查
- `GET /api/vector/stats` - 获取统计信息
- `GET /api/vector/health` - 健康检查

## API文档

启动后访问：http://localhost:8004/docs

## 依赖服务

- Milvus (19530) - 向量数据库
- 认证服务 (8001) - Token验证
- OpenAI API - 文本嵌入和AI回答

## 使用示例

### 语义搜索

```bash
curl -X POST "http://localhost:8004/api/vector/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "深度学习在计算机视觉中的应用",
    "top_k": 10
  }'
```

### 论文问答

```bash
curl -X POST "http://localhost:8004/api/vector/qa" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_id": "paper123.pdf",
    "question": "这篇论文的主要贡献是什么？",
    "top_k": 5
  }'
```

## 注意事项

- 确保Milvus服务已启动
- 确保OpenAI API密钥有效
- SECRET_KEY必须与认证服务保持一致

