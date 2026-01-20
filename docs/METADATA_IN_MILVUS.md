# Milvus 中的 Metadata 支持

## 概述

系统现在在 Milvus 中存储**丰富的 metadata**（元数据），检索时可以获取论文的详细信息，不仅仅是文本内容。

## Metadata 字段

### 完整字段列表

```python
{
    # 系统字段
    "id": 123456,                    # Milvus主键（自动生成）
    "distance": 0.234,               # 向量距离（越小越相似）
    "relevance_score": 0.810,        # 相关性分数（0-1，越大越相关）
    
    # Paper 基本信息
    "paper_id": "20260120_paper.pdf",      # MinIO对象名（唯一标识）
    "title": "Deep Learning for NLP",      # 论文标题
    "file_name": "paper.pdf",              # 原始文件名
    "upload_time": "2026-01-20T...",       # 上传时间（ISO 8601）
    
    # Chunk 信息
    "chunk_id": "20260120_paper.pdf#chunk_0",  # Chunk唯一ID
    "chunk_index": 0,                          # Chunk索引（从0开始）
    "content": "Abstract: This paper...",      # Chunk文本内容
    "chunk_chars": 987,                        # Chunk字符数
    "page_range": "1-3",                       # 页码范围（估算）
    "source": "chunk"                          # 来源类型
}
```

## 字段详解

### 1. Paper 基本信息

#### `paper_id` (VARCHAR 255)
- **含义**: 论文的唯一标识符（MinIO对象名）
- **格式**: `YYYYMMDD_HHMMSS_filename.pdf`
- **用途**: 
  - 关联同一篇论文的所有chunks
  - 删除论文时级联删除所有chunks
  - 在MinIO中定位原始PDF文件

#### `title` (VARCHAR 1000)
- **含义**: 论文标题
- **来源**: 从文件名提取（去除`.pdf`和`_`）
- **用途**: 
  - 显示给用户
  - 按论文分组展示
  - 搜索结果标题

#### `file_name` (VARCHAR 500)
- **含义**: 用户上传的原始文件名
- **格式**: `paper.pdf`
- **用途**: 
  - 显示用户友好的文件名
  - 下载时使用
  - 搜索和过滤

#### `upload_time` (VARCHAR 50)
- **含义**: 论文上传时间
- **格式**: ISO 8601 (`2026-01-20T12:34:56.789Z`)
- **用途**: 
  - 按时间排序
  - 显示"最近上传"
  - 时间范围过滤

### 2. Chunk 信息

#### `chunk_id` (VARCHAR 300)
- **含义**: Chunk的全局唯一标识
- **格式**: `{paper_id}#chunk_{index}`
- **用途**: 
  - 精确定位到某个chunk
  - 引用溯源
  - 去重

#### `chunk_index` (INT64)
- **含义**: Chunk在论文中的序号（从0开始）
- **用途**: 
  - 排序（按文档顺序）
  - 重组上下文
  - 显示"第N段"

#### `content` (VARCHAR 65535)
- **含义**: Chunk的文本内容
- **大小**: 最多65535字符（约16K tokens）
- **用途**: 
  - 显示搜索结果
  - RAG上下文
  - 文本分析

#### `chunk_chars` (INT64)
- **含义**: Chunk的实际字符数
- **范围**: 通常 800-1200（目标1000）
- **用途**: 
  - 质量检查
  - 统计分析
  - 计费估算

#### `page_range` (VARCHAR 50)
- **含义**: Chunk对应的页码范围（估算）
- **格式**: `"1-3"` 或 `"5-7"`
- **用途**: 
  - 显示来源位置
  - 快速定位
  - PDF导航

#### `source` (VARCHAR 100)
- **含义**: Chunk的来源类型
- **值**: `"chunk"` (当前都是chunk类型)
- **用途**: 
  - 区分不同类型的文本
  - 未来扩展（如"abstract", "figure_caption"等）

## 检索示例

### 1. 基础检索（获取所有metadata）

```python
from app.services.milvus_service import MilvusService
from app.services.openai_service import OpenAIService

# 初始化
milvus = MilvusService()
openai = OpenAIService()
milvus.connect()

# 生成查询向量
query = "What is transformer architecture?"
query_embedding = await openai.generate_embeddings([query])

# 检索（自动返回所有metadata）
results = milvus.search_similar(
    query_vectors=query_embedding,
    top_k=5
)

# 查看结果
for hit in results[0]:
    print(f"📄 {hit['file_name']}")
    print(f"   标题: {hit['title']}")
    print(f"   Chunk: #{hit['chunk_index']} (页码: {hit['page_range']})")
    print(f"   上传: {hit['upload_time']}")
    print(f"   相关性: {hit['relevance_score']:.2%}")
    print(f"   内容: {hit['content'][:200]}...")
    print()
```

**输出示例：**
```
📄 transformer_paper.pdf
   标题: Attention Is All You Need
   Chunk: #3 (页码: 2-4)
   上传: 2026-01-20T14:32:17.123Z
   相关性: 91.25%
   内容: The Transformer model architecture is based entirely on 
         attention mechanisms, dispensing with recurrence and 
         convolutions entirely...
```

### 2. 按论文分组展示

```python
# 检索后按paper_id分组
results = milvus.search_similar(query_vectors=query_embedding, top_k=20)

papers = {}
for hit in results[0]:
    paper_id = hit['paper_id']
    if paper_id not in papers:
        papers[paper_id] = {
            'file_name': hit['file_name'],
            'title': hit['title'],
            'upload_time': hit['upload_time'],
            'chunks': []
        }
    papers[paper_id]['chunks'].append({
        'chunk_index': hit['chunk_index'],
        'page_range': hit['page_range'],
        'content': hit['content'],
        'relevance': hit['relevance_score']
    })

# 显示
for paper_id, paper in papers.items():
    print(f"\n📚 {paper['file_name']}")
    print(f"   {paper['title']}")
    print(f"   相关片段 ({len(paper['chunks'])}个):")
    for chunk in paper['chunks'][:3]:  # 只显示前3个
        print(f"     - Chunk #{chunk['chunk_index']} (页码: {chunk['page_range']})")
        print(f"       相关性: {chunk['relevance']:.2%}")
```

### 3. 时间范围过滤

```python
from datetime import datetime, timedelta

# 获取最近7天的论文
seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'

# 检索并过滤
results = milvus.search_similar(query_vectors=query_embedding, top_k=50)

recent_results = [
    hit for hit in results[0]
    if hit['upload_time'] >= seven_days_ago
]

print(f"最近7天上传的相关论文: {len(recent_results)}篇")
```

### 4. 构建 RAG Context（带metadata）

```python
async def build_rag_context(chunks: List[Dict]) -> str:
    """构建RAG上下文（包含metadata）"""
    
    context_parts = []
    
    for i, chunk in enumerate(chunks):
        # 包含来源信息
        source_info = (
            f"[来源 {i+1}] {chunk['file_name']}\n"
            f"标题: {chunk['title']}\n"
            f"位置: 第 {chunk['chunk_index']+1} 段 (页码: {chunk['page_range']})\n"
            f"上传时间: {chunk['upload_time'][:10]}\n"
            f"相关性: {chunk['relevance_score']:.1%}\n"
            f"\n{chunk['content']}\n"
        )
        context_parts.append(source_info)
    
    return "\n" + "="*60 + "\n\n".join(context_parts)

# 使用
chunks = results[0][:5]
context = await build_rag_context(chunks)

prompt = f"""基于以下参考文献回答问题。

{context}

问题: {query}

请提供详细回答，并注明信息来源（使用 [来源 N] 引用）。
"""
```

## 高级用法

### 1. 引用溯源

```python
def generate_citation(chunk: Dict) -> str:
    """生成引用格式"""
    return (
        f"{chunk['file_name']} "
        f"(上传于 {chunk['upload_time'][:10]}), "
        f"第 {chunk['chunk_index']+1} 段, "
        f"页码 {chunk['page_range']}"
    )

# 使用
for hit in results[0][:3]:
    print(f"内容: {hit['content'][:100]}...")
    print(f"引用: {generate_citation(hit)}")
```

### 2. 去重（避免同一论文多个chunks）

```python
def deduplicate_by_paper(results: List[Dict], max_per_paper: int = 2) -> List[Dict]:
    """每篇论文最多保留N个chunks"""
    
    paper_counts = {}
    deduplicated = []
    
    for hit in results:
        paper_id = hit['paper_id']
        count = paper_counts.get(paper_id, 0)
        
        if count < max_per_paper:
            deduplicated.append(hit)
            paper_counts[paper_id] = count + 1
    
    return deduplicated

# 使用
results = milvus.search_similar(query_vectors=query_embedding, top_k=20)
unique_results = deduplicate_by_paper(results[0], max_per_paper=2)
```

### 3. 智能排序

```python
def smart_sort(chunks: List[Dict]) -> List[Dict]:
    """
    智能排序：
    1. 按相关性分组
    2. 同一论文的chunks按chunk_index排序
    """
    
    # 按paper_id分组
    papers = {}
    for chunk in chunks:
        pid = chunk['paper_id']
        if pid not in papers:
            papers[pid] = []
        papers[pid].append(chunk)
    
    # 每个论文内部按chunk_index排序
    for pid in papers:
        papers[pid].sort(key=lambda x: x['chunk_index'])
    
    # 按第一个chunk的相关性排序论文
    sorted_papers = sorted(
        papers.items(),
        key=lambda x: x[1][0]['relevance_score'],
        reverse=True
    )
    
    # 展平
    result = []
    for pid, paper_chunks in sorted_papers:
        result.extend(paper_chunks)
    
    return result
```

## API 集成示例

### 创建搜索 API

```python
from fastapi import APIRouter, Query
from typing import List, Optional

router = APIRouter(prefix="/api/papers", tags=["papers"])

@router.post("/search")
async def semantic_search(
    query: str,
    top_k: int = Query(10, ge=1, le=50),
    uploaded_after: Optional[str] = None
):
    """
    语义搜索API（返回完整metadata）
    
    Args:
        query: 搜索查询
        top_k: 返回结果数量
        uploaded_after: 过滤上传时间（ISO格式）
    
    Returns:
        {
            "query": "...",
            "results": [
                {
                    "paper_id": "...",
                    "file_name": "...",
                    "title": "...",
                    "chunk_index": 0,
                    "page_range": "1-3",
                    "upload_time": "...",
                    "relevance_score": 0.95,
                    "content": "...",
                    ...
                }
            ],
            "total": 10
        }
    """
    # 生成查询向量
    openai_service = get_openai_service()
    query_embedding = await openai_service.generate_embeddings([query])
    
    # 检索
    milvus_service = get_milvus_service()
    results = milvus_service.search_similar(
        query_vectors=query_embedding,
        top_k=top_k
    )
    
    # 过滤（如果有时间限制）
    chunks = results[0]
    if uploaded_after:
        chunks = [c for c in chunks if c['upload_time'] >= uploaded_after]
    
    return {
        "query": query,
        "results": chunks,
        "total": len(chunks)
    }
```

## 前端展示示例

### Vue 组件

```vue
<template>
  <div class="search-results">
    <div v-for="result in results" :key="result.chunk_id" class="result-card">
      <!-- Paper信息 -->
      <div class="paper-info">
        <h3>{{ result.title }}</h3>
        <div class="metadata">
          <span class="file-name">📄 {{ result.file_name }}</span>
          <span class="upload-time">🕒 {{ formatDate(result.upload_time) }}</span>
          <span class="relevance">⭐ {{ (result.relevance_score * 100).toFixed(1) }}%</span>
        </div>
      </div>
      
      <!-- Chunk信息 -->
      <div class="chunk-info">
        <span class="chunk-badge">
          Chunk #{{ result.chunk_index + 1 }} 
          (页码: {{ result.page_range }})
        </span>
      </div>
      
      <!-- 内容 -->
      <div class="content">
        {{ result.content }}
      </div>
      
      <!-- 操作 -->
      <div class="actions">
        <button @click="viewPaper(result.paper_id)">查看全文</button>
        <button @click="copyReference(result)">复制引用</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    formatDate(isoString) {
      return new Date(isoString).toLocaleDateString('zh-CN')
    },
    
    copyReference(result) {
      const ref = `${result.file_name}, 第${result.chunk_index + 1}段 (页码: ${result.page_range})`
      navigator.clipboard.writeText(ref)
    }
  }
}
</script>
```

## 性能优化

### 1. 只返回需要的字段

```python
# 如果只需要部分字段
results = milvus_service.collection.search(
    data=query_vectors,
    anns_field="embedding",
    limit=10,
    output_fields=["paper_id", "title", "content"]  # 只返回这3个字段
)
```

### 2. 缓存metadata

```python
# 缓存论文的基本信息
paper_cache = {}

def get_paper_metadata(paper_id: str) -> Dict:
    if paper_id not in paper_cache:
        # 从Milvus查询该论文的任意一个chunk获取metadata
        results = milvus.collection.query(
            expr=f'paper_id == "{paper_id}"',
            output_fields=["title", "file_name", "upload_time"],
            limit=1
        )
        paper_cache[paper_id] = results[0]
    
    return paper_cache[paper_id]
```

## 总结

通过丰富的 metadata，系统现在可以：

✅ **精确溯源** - 知道内容来自哪篇论文的哪一页  
✅ **智能排序** - 按相关性、时间等多维度排序  
✅ **用户友好** - 显示原始文件名和上传时间  
✅ **引用支持** - 自动生成学术引用格式  
✅ **过滤筛选** - 按时间、来源等条件过滤  
✅ **RAG增强** - 提供丰富的上下文信息  

这些 metadata 让检索结果更加实用和专业！🎯

