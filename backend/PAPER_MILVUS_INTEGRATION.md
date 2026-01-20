# Paper Library - Milvus 集成说明

## 功能简介

Paper Library 页面现在支持自动将上传的论文存储到 Milvus 向量数据库，实现语义搜索和智能推荐功能。

## 主要改动

### 1. OpenAI Service (`app/services/openai_service.py`)

新增 `generate_embeddings` 方法：
- 使用 `text-embedding-3-small` 模型
- 支持批量生成文本嵌入向量
- 向量维度：1536

### 2. Papers API (`app/api/papers.py`)

#### 新增功能：
- `extract_text_from_pdf()`: 从 PDF 提取文本（前3页）
- `store_paper_in_milvus()`: 将论文存储到 Milvus
- `get_milvus_service()`: Milvus 服务实例管理
- `get_openai_service()`: OpenAI 服务实例管理

#### 修改的接口：

**上传接口** (`POST /api/papers/upload`)
```python
# 现在会自动：
1. 存储 PDF 到 MinIO
2. 提取 PDF 文本
3. 生成嵌入向量
4. 存储到 Milvus
```

**删除接口** (`DELETE /api/papers/delete/{object_name}`)
```python
# 现在会自动：
1. 从 MinIO 删除文件
2. 从 Milvus 删除向量数据
```

## 数据流程

```
用户上传PDF
    ↓
[1] 存储到 MinIO ✓
    ↓
[2] 提取 PDF 文本（前3页，最多5000字符）
    ↓
[3] 生成嵌入向量（OpenAI text-embedding-3-small）
    ↓
[4] 存储到 Milvus ✓
    ↓
返回成功响应
```

## Milvus 数据结构

```python
Collection: research_papers
Schema:
  - id: INT64 (主键, 自增)
  - paper_id: VARCHAR(255) (MinIO 对象名)
  - embedding: FLOAT_VECTOR(1536) (嵌入向量)
  - title: VARCHAR(1000) (论文标题，从文件名提取)
  - abstract: VARCHAR(65535) (摘要，文本前500字符)
  - source: VARCHAR(100) (来源类型: "full_text")

Index: IVF_FLAT (L2 距离)
```

## 配置要求

### 1. 环境变量 (`.env`)

```env
# OpenAI API
OPENAI_API_KEY=sk-xxx...
OPENAI_MODEL=gpt-4o

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 2. 启动服务

```bash
# 启动 Milvus
docker-compose up -d milvus-standalone

# 启动 MinIO
docker-compose up -d minio

# 启动后端
cd backend
python run.py
```

## 测试

### 运行测试脚本

```bash
cd backend
python test_paper_upload_milvus.py
```

测试内容：
- ✓ Milvus 连接和集合创建
- ✓ OpenAI 嵌入生成
- ✓ 完整工作流程（插入、搜索、删除）

### 手动测试

1. 访问前端：http://localhost:5173
2. 进入 Paper Library 页面
3. 上传一个 PDF 文件
4. 检查后端日志，应该看到：
   ```
   Uploading file: xxx.pdf
   Extracting text from PDF: xxx.pdf
   Generating embeddings for: xxx.pdf
   Storing paper in Milvus: xxx.pdf
   Successfully stored paper in Milvus: xxx.pdf
   ```

## 错误处理

### 容错设计
- Milvus 存储失败**不会影响**上传成功
- OpenAI API 失败会跳过向量存储
- PDF 文本提取失败会跳过向量存储

### 日志级别
- `INFO`: 正常操作日志
- `WARNING`: 可恢复的错误（如文本提取失败）
- `ERROR`: 严重错误（但不影响主流程）

## 性能考虑

1. **异步处理**: Milvus 存储不阻塞上传响应
2. **文本限制**: 只提取前3页，最多5000字符
3. **服务复用**: 使用单例模式管理服务实例
4. **延迟初始化**: 只在需要时初始化 Milvus 和 OpenAI 服务

## 依赖包

已在 `requirements.txt` 中包含：
```
pymilvus>=2.6.6
pdfplumber==0.11.0
openai==1.54.0
```

## 未来扩展

1. **语义搜索**: 在前端添加基于向量的搜索功能
2. **相似推荐**: 推荐相似的论文
3. **批量上传**: 优化批量上传的向量生成
4. **增量更新**: 支持更新已存在论文的向量
5. **多模态**: 支持图片、表格等内容的向量化

## 故障排查

### Milvus 连接失败
```bash
# 检查服务状态
docker-compose ps milvus-standalone

# 查看日志
docker-compose logs milvus-standalone

# 重启服务
docker-compose restart milvus-standalone
```

### OpenAI API 错误
```bash
# 检查 API Key
echo $OPENAI_API_KEY

# 测试连接
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### 查看详细日志
```bash
# 后端日志
tail -f backend/logs/app.log

# 过滤 Milvus 相关日志
tail -f backend/logs/app.log | grep -i milvus
```

## 相关文档

- [完整功能文档](../docs/PAPER_UPLOAD_MILVUS.md)
- [Milvus 设置指南](../docs/MILVUS_SETUP.md)
- [Milvus 使用说明](../docs/MILVUS_USAGE.md)

