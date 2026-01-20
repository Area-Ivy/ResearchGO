# Paper Library 上传到 Milvus 功能说明

## 功能概述

当用户在 Paper Library 页面上传 PDF 论文时，系统会自动：

1. **存储到 MinIO**：将 PDF 文件存储到 MinIO 对象存储
2. **提取文本**：从 PDF 中提取文本内容（前3页）
3. **生成嵌入**：使用 OpenAI 的 `text-embedding-3-small` 模型生成向量嵌入
4. **存储到 Milvus**：将向量和元数据存储到 Milvus 向量数据库

## 技术实现

### 1. 文本嵌入生成

在 `OpenAIService` 中添加了 `generate_embeddings` 方法：

```python
async def generate_embeddings(
    self,
    texts: List[str],
    model: str = "text-embedding-3-small"
) -> List[List[float]]:
    """生成文本嵌入向量"""
```

- **模型**：`text-embedding-3-small`
- **维度**：1536
- **优势**：成本低、速度快、效果好

### 2. PDF 文本提取

使用 `pdfplumber` 库提取 PDF 文本：

```python
async def extract_text_from_pdf(pdf_data: bytes, max_chars: int = 5000) -> str:
    """从 PDF 中提取文本内容（前3页）"""
```

- 只提取前3页以获取标题和摘要
- 限制最大字符数为 5000
- 避免处理过大的文本

### 3. Milvus 存储

存储的数据结构：

```python
{
    "paper_id": "MinIO对象名",
    "embedding": [1536维向量],
    "title": "论文标题（从文件名提取）",
    "abstract": "论文摘要（文本前500字符）",
    "source": "full_text"
}
```

### 4. 上传流程

```
用户上传PDF
    ↓
读取文件数据
    ↓
存储到MinIO ✓
    ↓
提取PDF文本
    ↓
生成嵌入向量
    ↓
存储到Milvus ✓
    ↓
返回成功响应
```

**注意**：Milvus 存储失败不会影响上传结果，只会记录错误日志。

### 5. 删除流程

删除论文时会同时：
- 从 MinIO 删除 PDF 文件
- 从 Milvus 删除对应的向量数据

## 配置要求

### 环境变量

确保 `.env` 文件中配置了以下变量：

```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 服务依赖

1. **Milvus**：向量数据库服务
   ```bash
   docker-compose up -d milvus-standalone
   ```

2. **MinIO**：对象存储服务
   ```bash
   docker-compose up -d minio
   ```

3. **OpenAI API**：需要有效的 API Key

## 测试

运行测试脚本验证功能：

```bash
cd backend
python test_paper_upload_milvus.py
```

测试内容：
1. ✓ Milvus 连接测试
2. ✓ OpenAI 嵌入生成测试
3. ✓ 完整工作流程测试（插入、搜索、删除）

## 使用示例

### 前端上传

用户在 Paper Library 页面拖拽或选择 PDF 文件上传，系统自动处理。

### API 调用

```bash
# 上传论文
curl -X POST "http://localhost:8000/api/papers/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@paper.pdf"

# 响应
{
  "object_name": "20260120_123456_paper.pdf",
  "original_name": "paper.pdf",
  "size": 1234567,
  "content_type": "application/pdf",
  "upload_time": "2026-01-20T12:34:56",
  "message": "File uploaded successfully"
}
```

## 数据结构

### Milvus 集合 Schema

```python
Collection: research_papers
Fields:
  - id: INT64 (主键, 自动生成)
  - paper_id: VARCHAR(255) (论文ID, MinIO对象名)
  - embedding: FLOAT_VECTOR(1536) (向量嵌入)
  - title: VARCHAR(1000) (论文标题)
  - abstract: VARCHAR(65535) (论文摘要)
  - source: VARCHAR(100) (来源类型)

Index: IVF_FLAT
Metric: L2
```

## 性能优化

1. **异步处理**：Milvus 存储不阻塞上传响应
2. **文本限制**：只提取前3页，限制5000字符
3. **批量处理**：支持批量生成嵌入（未来扩展）
4. **错误隔离**：Milvus 失败不影响上传成功

## 错误处理

- **PDF 文本提取失败**：记录警告，跳过 Milvus 存储
- **嵌入生成失败**：记录错误，跳过 Milvus 存储
- **Milvus 存储失败**：记录错误，不影响上传结果
- **服务不可用**：自动跳过 Milvus 存储

## 未来扩展

1. **增量更新**：支持更新已存在论文的向量
2. **批量上传**：优化批量上传的向量生成
3. **多模态嵌入**：支持图片、表格等多模态内容
4. **语义搜索**：在前端添加基于向量的语义搜索功能
5. **相似论文推荐**：基于向量相似度推荐相关论文

## 故障排查

### 1. Milvus 连接失败

```bash
# 检查 Milvus 服务状态
docker-compose ps milvus-standalone

# 查看日志
docker-compose logs milvus-standalone
```

### 2. OpenAI API 错误

```bash
# 检查 API Key
echo $OPENAI_API_KEY

# 测试 API 连接
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### 3. 查看后端日志

```bash
# 查看上传日志
tail -f backend/logs/app.log | grep "Uploading\|Milvus\|embedding"
```

## 相关文档

- [Milvus 设置指南](./MILVUS_SETUP.md)
- [Milvus 使用说明](./MILVUS_USAGE.md)
- [MinIO 设置指南](./MINIO_SETUP.md)
- [快速开始](./QUICK_START.md)

