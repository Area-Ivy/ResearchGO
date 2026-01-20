# Chunk-Based Paper Upload - 快速开始

## 🎯 新功能

Paper Library 现在支持**智能文本切分**，每篇论文会被自动切分成多个 chunks（文本块），为未来的 RAG 问答系统做好准备！

## 🆚 对比：之前 vs 现在

### 之前（简单版本）
```
一篇论文 → 1个向量 → Milvus
```
- ❌ 无法精确定位段落
- ❌ 长文档无法完整处理
- ❌ 检索粒度太粗

### 现在（Chunk版本）
```
一篇论文 → N个chunks → N个向量 → Milvus
```
- ✅ 精确定位到具体段落
- ✅ 支持任意长度文档
- ✅ 检索粒度精细
- ✅ 为RAG系统做好准备

## 🚀 快速开始

### 1. 确保服务运行

```bash
# 启动 Milvus 和 MinIO
docker-compose up -d milvus-standalone minio

# 检查服务状态
docker-compose ps
```

### 2. 重要：需要重新创建 Milvus 集合

由于 schema 改变，需要删除旧集合：

```bash
cd backend
python -c "
from app.services.milvus_service import MilvusService
service = MilvusService()
service.connect()
service.drop_collection()
print('✓ 旧集合已删除')
"
```

或者在 Python 中：

```python
from app.services.milvus_service import MilvusService
service = MilvusService()
service.connect()
service.drop_collection()
service.disconnect()
```

### 3. 运行测试

```bash
cd backend
python test_paper_upload_with_chunks.py
```

**预期输出：**
```
==================================================================
Paper Upload to Milvus with Chunks - 功能测试
==================================================================

=== 测试文本切分器 ===
测试滑动窗口切分:
✓ 生成了 10 个chunks
  Chunk 0: 495 字符, 位置 0-495
  ...

=== 测试 Milvus 存储 Chunks ===
✓ 成功连接到 Milvus
✓ 集合创建/验证成功
✓ 索引创建成功

=== 测试完整工作流程（带 Chunks）===
切分文本成chunks...
✓ 生成了 8 个chunks
生成嵌入向量...
✓ 生成了 8 个嵌入向量，维度: 1536
存储chunks到 Milvus...
✓ 成功存储 8 个chunks到 Milvus
...

==================================================================
测试总结:
  文本切分器测试: ✓ 通过
  Milvus连接测试: ✓ 通过
  完整工作流程测试: ✓ 通过
  Chunk检索测试: ✓ 通过
==================================================================

✓ 所有测试通过！系统已准备好处理带chunk的论文上传。
```

### 4. 启动应用

```bash
# 启动后端
cd backend
python run.py

# 启动前端（另一个终端）
cd frontend
npm run dev
```

### 5. 上传论文测试

1. 访问 http://localhost:5173
2. 进入 Paper Library 页面
3. 上传一个 PDF 文件
4. 查看后端日志

**后端日志示例：**
```
Uploading file: paper.pdf
Extracting text from PDF: paper.pdf
Extracting text from 50 pages (total: 150)
Extracted 45678 characters from PDF
Splitting text into chunks (size: 1000, overlap: 200)
Generated 52 chunks for paper.pdf
Generating embeddings for 52 chunks
Successfully stored 52 chunks in Milvus: paper.pdf
```

## 📊 Chunk 切分详解

### 配置参数

```python
# 在 papers.py 的 store_paper_in_milvus 函数中
chunk_size=1000        # 每个chunk 1000字符
chunk_overlap=200      # 重叠 200字符
max_pages=50           # 最多提取 50页
```

### 为什么需要重叠？

```
Chunk 1: [                    ]
Chunk 2:         [                    ]
Chunk 3:                  [                    ]
              ↑ 重叠区域保持上下文连贯
```

**好处：**
- 避免重要信息在边界被切断
- 保持语义完整性
- 提高检索质量

### Chunk 数据结构

每个 chunk 包含：
```python
{
    'text': "实际的文本内容...",
    'chunk_index': 0,           # chunk序号
    'start_pos': 0,             # 在原文中的起始位置
    'end_pos': 1000,            # 在原文中的结束位置
    'total_chars': 987          # 实际字符数
}
```

## 🔍 检索示例

### 1. 基础检索

```python
from app.services.milvus_service import MilvusService
from app.services.openai_service import OpenAIService

# 初始化服务
milvus = MilvusService()
openai = OpenAIService()
milvus.connect()

# 查询
query = "What is transformer architecture?"
query_embedding = await openai.generate_embeddings([query])

# 检索
results = milvus.search_similar(
    query_vectors=query_embedding,
    top_k=5
)

# 查看结果
for hit in results[0]:
    print(f"Paper: {hit['title']}")
    print(f"Chunk: {hit['chunk_index']}")
    print(f"Content: {hit['content'][:200]}...")
    print(f"Relevance: {1 / (1 + hit['distance']):.3f}")
    print()
```

### 2. 按论文查看所有 chunks

```python
# 查询特定论文的所有chunks
paper_id = "20260120_143217_paper.pdf"

# 可以通过 paper_id 过滤
# 然后按 chunk_index 排序
# 重组完整文本
```

## 📈 性能数据

### 处理时间

**单篇论文（30页）：**
- PDF文本提取: ~2秒
- 切分成chunks: ~0.1秒
- 生成嵌入(30 chunks): ~3秒
- 存储到Milvus: ~0.2秒
- **总计**: ~5.3秒

### API 成本

**每篇论文（假设30 chunks）：**
- 嵌入生成: ~$0.0009
- **1000篇论文**: ~$0.90

## 🎯 下一步：构建 RAG

系统已经为 RAG 做好准备，接下来可以实现：

### 1. 语义搜索 API
```python
@router.post("/api/papers/search")
async def semantic_search(query: str, top_k: int = 10):
    """语义搜索论文片段"""
    pass
```

### 2. RAG 问答 API
```python
@router.post("/api/papers/ask")
async def ask_question(question: str):
    """基于论文库回答问题"""
    # 1. 检索相关chunks
    # 2. 构建context
    # 3. 生成回答
    pass
```

### 3. 前端集成
- 添加语义搜索框
- 显示相关chunks
- 实现问答界面
- 展示来源引用

## 🐛 常见问题

### Q: 上传后没有生成 chunks？

**检查：**
```bash
# 查看后端日志
tail -f backend/logs/app.log | grep -E "chunks|Extracting|Splitting"

# 常见原因：
# 1. PDF是扫描版（无法提取文本）
# 2. OpenAI API失败
# 3. Milvus连接失败
```

### Q: 如何查看某篇论文的所有 chunks？

```python
# 使用 Attu (Milvus GUI) 或者
from app.services.milvus_service import MilvusService

service = MilvusService()
service.connect()

# 查询（需要实现过滤功能）
# paper_id = "your_paper_id"
# chunks = service.query(f"paper_id == '{paper_id}'")
```

### Q: Chunk 切分太小或太大？

修改 `backend/app/api/papers.py` 中的参数：

```python
async def store_paper_in_milvus(
    ...
    chunk_size=1500,        # 改为1500字符
    chunk_overlap=300,      # 改为300字符重叠
    max_pages=100           # 改为提取100页
):
```

### Q: 需要重新处理已上传的论文？

```bash
# 1. 下载论文
# 2. 删除旧记录
# 3. 重新上传

# 或者编写批量重处理脚本
```

## 📚 相关文档

- [Chunk-Based RAG 系统设计](docs/CHUNK_BASED_RAG.md)
- [文本切分器 API](backend/app/utils/text_chunker.py)
- [Milvus Schema 说明](backend/app/services/milvus_service.py)

## ✨ 总结

新的 chunk 系统带来：

✅ **更精确的检索** - 段落级别匹配  
✅ **更好的扩展性** - 支持长文档  
✅ **RAG 就绪** - 为问答系统打下基础  
✅ **更低成本** - 按需检索相关片段  

现在开始上传论文，系统会自动处理一切！🚀

