# Chunk-Based RAG 系统设计文档

## 概述

本文档详细说明了基于 chunk 切分的论文存储和检索系统，为构建 RAG（Retrieval-Augmented Generation）系统做好准备。

## 系统架构

```
论文上传
    ↓
PDF文本提取（最多50页）
    ↓
文本切分（1000字符/chunk，200字符重叠）
    ↓
批量生成嵌入向量（OpenAI text-embedding-3-small）
    ↓
存储到Milvus（每个chunk一条记录）
    ↓
支持语义检索和RAG问答
```

## Chunk 切分策略

### 1. 切分参数

```python
CHUNK_SIZE = 1000        # 每个chunk的字符数
CHUNK_OVERLAP = 200      # chunk之间的重叠字符数
MAX_CHUNKS = 100         # 每篇论文最多100个chunks
MAX_PAGES = 50           # 最多提取50页
```

### 2. 切分方法

#### 滑动窗口法（默认）
```python
split_text_into_chunks(
    text=text,
    chunk_size=1000,
    chunk_overlap=200,
    method="sliding_window"
)
```

**特点：**
- 固定大小的chunk
- 保持上下文连续性（通过重叠）
- 适合大多数文档类型

#### 段落切分法
```python
split_text_into_chunks(
    text=text,
    chunk_size=1000,
    method="paragraphs"
)
```

**特点：**
- 在自然段落边界切分
- 保持语义完整性
- 适合结构化文档

### 3. 智能切分点选择

优先级顺序：
1. **段落分隔符** (`\n\n`) - 最自然的切分点
2. **句子结束符** (`。！？.!?`) - 保持句子完整
3. **逗号/分号** (`，；,;`) - 次优选择
4. **空格** - 避免在单词中间切分

## Milvus 数据结构

### Collection Schema

```python
Collection: research_papers
Fields:
  - id: INT64 (主键, 自增)
  - paper_id: VARCHAR(255) (论文ID，MinIO对象名)
  - chunk_id: VARCHAR(300) (Chunk唯一ID: paper_id#chunk_index)
  - chunk_index: INT64 (Chunk索引，从0开始)
  - embedding: FLOAT_VECTOR(1536) (嵌入向量)
  - title: VARCHAR(1000) (论文标题)
  - content: VARCHAR(65535) (Chunk文本内容)
  - chunk_chars: INT64 (Chunk字符数)
  - source: VARCHAR(100) (来源类型: "chunk")

Index: IVF_FLAT (L2距离)
```

### 数据示例

```json
{
  "id": 123456,
  "paper_id": "20260120_143217_paper.pdf",
  "chunk_id": "20260120_143217_paper.pdf#chunk_0",
  "chunk_index": 0,
  "embedding": [0.123, -0.456, ...], // 1536维向量
  "title": "Deep Learning for NLP",
  "content": "Abstract: This paper presents...",
  "chunk_chars": 987,
  "source": "chunk"
}
```

## 检索策略

### 1. 语义检索

```python
# 用户查询
query = "How does attention mechanism work in transformers?"

# 生成查询向量
query_embedding = await openai_service.generate_embeddings([query])

# 检索相似chunks
results = milvus_service.search_similar(
    query_vectors=query_embedding,
    top_k=5  # 返回最相似的5个chunks
)

# 结果格式
[
  {
    "paper_id": "paper_001.pdf",
    "chunk_id": "paper_001.pdf#chunk_3",
    "chunk_index": 3,
    "title": "Transformer Architecture",
    "content": "The attention mechanism allows...",
    "distance": 0.234
  },
  ...
]
```

### 2. 混合检索（未来实现）

```python
# 结合关键词和语义检索
# 1. 使用BM25进行关键词匹配
# 2. 使用向量相似度进行语义匹配
# 3. 融合两种结果（如RRF算法）
```

### 3. 重排序（Re-ranking）

```python
# 对检索结果进行重排序
# 1. 使用cross-encoder模型
# 2. 考虑chunk的位置信息
# 3. 考虑同一paper中相邻chunks的相关性
```

## RAG 工作流程

### 1. 检索阶段（Retrieval）

```python
async def retrieve_relevant_chunks(query: str, top_k: int = 5):
    """检索相关chunks"""
    
    # 1. 生成查询向量
    query_embedding = await openai_service.generate_embeddings([query])
    
    # 2. 向量检索
    results = milvus_service.search_similar(
        query_vectors=query_embedding,
        top_k=top_k
    )
    
    # 3. 提取chunks
    chunks = []
    for hit in results[0]:
        chunks.append({
            "paper_id": hit["paper_id"],
            "chunk_index": hit["chunk_index"],
            "content": hit["content"],
            "title": hit["title"],
            "relevance": 1 / (1 + hit["distance"])  # 转换为相关性分数
        })
    
    return chunks
```

### 2. 上下文构建

```python
async def build_context(chunks: List[Dict]) -> str:
    """构建RAG上下文"""
    
    context_parts = []
    
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[文档 {i+1}] {chunk['title']}\n"
            f"{chunk['content']}\n"
        )
    
    return "\n---\n".join(context_parts)
```

### 3. 生成阶段（Generation）

```python
async def generate_answer(query: str, context: str) -> str:
    """基于检索到的context生成回答"""
    
    prompt = f"""基于以下参考文献，回答用户的问题。

参考文献：
{context}

用户问题：{query}

请提供详细、准确的回答，并注明信息来源于哪篇文献。如果参考文献中没有相关信息，请明确说明。
"""
    
    messages = [
        ChatMessage(role="system", content="你是一位专业的学术助手。"),
        ChatMessage(role="user", content=prompt)
    ]
    
    response = await openai_service.chat_completion(
        messages=messages,
        temperature=0.3,
        max_tokens=2000
    )
    
    return response
```

### 4. 完整RAG流程

```python
async def rag_query(query: str) -> Dict:
    """完整的RAG查询流程"""
    
    # 1. 检索
    chunks = await retrieve_relevant_chunks(query, top_k=5)
    
    # 2. 构建上下文
    context = await build_context(chunks)
    
    # 3. 生成回答
    answer = await generate_answer(query, context)
    
    # 4. 返回结果
    return {
        "answer": answer,
        "sources": chunks,
        "query": query
    }
```

## 性能优化

### 1. 批量处理

```python
# 批量生成嵌入（降低API调用次数）
embeddings = await openai_service.generate_embeddings(chunk_texts)
# 而不是逐个生成
```

### 2. 缓存策略

```python
# 缓存常见查询的结果
# 使用Redis或内存缓存
```

### 3. 索引优化

```python
# 使用更高效的索引类型
milvus_service.create_index(
    index_type="HNSW",  # 更快的近似检索
    metric_type="COSINE"
)
```

### 4. 异步处理

```python
# 使用asyncio并发处理多个请求
async def process_multiple_queries(queries: List[str]):
    tasks = [rag_query(q) for q in queries]
    return await asyncio.gather(*tasks)
```

## 成本估算

### OpenAI API 成本

**嵌入生成：**
- 模型：text-embedding-3-small
- 价格：$0.00002 per 1K tokens
- 每篇论文（10 chunks）：~$0.0003
- 1000篇论文：~$0.30

**答案生成：**
- 模型：gpt-4o
- 价格：$5.00 per 1M input tokens, $15.00 per 1M output tokens
- 每次查询（5 chunks context）：~$0.005
- 1000次查询：~$5.00

## 使用示例

### 1. 上传论文（自动切分）

```python
# 前端上传PDF → 后端自动处理
# 1. 提取文本（最多50页）
# 2. 切分成chunks（1000字符，200重叠）
# 3. 生成嵌入向量
# 4. 存储到Milvus
```

### 2. 语义搜索

```python
# 搜索相关论文片段
results = await search_chunks(
    query="transformer attention mechanism",
    top_k=10
)

# 返回最相关的10个chunks
# 可以按paper_id分组展示
```

### 3. RAG 问答

```python
# 基于论文库回答问题
answer = await rag_query(
    query="What are the main advantages of transformers over RNNs?"
)

# 返回：
# - answer: 详细回答
# - sources: 参考的chunks
# - query: 原始问题
```

## 扩展计划

### 短期（1-2周）
- [ ] 实现基础的语义搜索API
- [ ] 添加chunk检索和展示
- [ ] 实现简单的RAG问答

### 中期（1-2个月）
- [ ] 混合检索（BM25 + 向量）
- [ ] 结果重排序
- [ ] 多轮对话支持
- [ ] 引用溯源

### 长期（3-6个月）
- [ ] 多模态检索（图片、表格）
- [ ] 知识图谱集成
- [ ] 个性化推荐
- [ ] 协作式标注

## 测试

```bash
# 运行测试
cd backend
python test_paper_upload_with_chunks.py

# 预期输出：
# ✓ 文本切分器测试通过
# ✓ Milvus连接测试通过
# ✓ 完整工作流程测试通过
# ✓ Chunk检索测试通过
```

## 故障排查

### 问题1：Chunk切分失败
```python
# 检查文本是否为空
# 检查chunk_size设置是否合理
# 查看日志中的详细错误信息
```

### 问题2：嵌入生成失败
```python
# 检查OpenAI API Key
# 检查文本长度是否超过限制
# 检查批量大小是否过大
```

### 问题3：Milvus存储失败
```python
# 检查schema是否正确
# 检查字段类型是否匹配
# 查看Milvus日志
```

## 相关文档

- [Paper Upload Milvus 功能说明](./PAPER_UPLOAD_MILVUS.md)
- [Milvus 设置指南](./MILVUS_SETUP.md)
- [Text Chunker API文档](../backend/app/utils/text_chunker.py)

## 总结

通过 chunk 切分方案，系统现在支持：

✅ **精确检索**：段落级别的精确匹配  
✅ **上下文保持**：重叠区域保持语义连贯  
✅ **可扩展性**：支持任意长度的文档  
✅ **RAG就绪**：为问答系统提供基础  
✅ **高效存储**：每个chunk独立向量化  

系统已经为构建高质量的 RAG 问答系统做好准备！

