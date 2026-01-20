# Milvus 向量数据库使用指南

## 📖 目录

1. [基本概念](#基本概念)
2. [快速开始](#快速开始)
3. [核心操作](#核心操作)
4. [向量嵌入生成](#向量嵌入生成)
5. [实战示例](#实战示例)
6. [最佳实践](#最佳实践)

## 基本概念

### 什么是向量数据库？

向量数据库用于存储和检索高维向量数据，特别适合：
- 🔍 **语义搜索**：根据文本含义而非关键词搜索
- 📄 **文档相似度**：查找相似的论文、文章
- 🖼️ **图像检索**：以图搜图
- 💬 **推荐系统**：内容推荐

### Milvus 核心概念

```
Collection（集合）
    ├── Field（字段）
    │   ├── 主键字段（id）
    │   ├── 向量字段（embedding）
    │   └── 标量字段（title, abstract...）
    └── Index（索引）
        └── 加速向量搜索
```

## 快速开始

### 1. 安装依赖

```bash
pip install pymilvus sentence-transformers
```

### 2. 连接到 Milvus

```python
from pymilvus import connections, Collection

# 连接到 Milvus
connections.connect(
    alias="default",
    host="localhost",
    port="19530"
)

print("✅ 连接成功！")
```

### 3. 创建集合

```python
from pymilvus import CollectionSchema, FieldSchema, DataType

# 定义字段
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="paper_id", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="abstract", dtype=DataType.VARCHAR, max_length=5000),
]

# 创建 schema
schema = CollectionSchema(fields, description="论文向量集合")

# 创建集合
from pymilvus import Collection
collection = Collection(name="papers", schema=schema)

print("✅ 集合创建成功！")
```

## 核心操作

### 1️⃣ 创建索引

索引是加速搜索的关键！

```python
# IVF_FLAT 索引 - 平衡精度和速度
index_params = {
    "metric_type": "L2",      # 距离度量：L2（欧氏距离）或 IP（内积）
    "index_type": "IVF_FLAT", # 索引类型
    "params": {"nlist": 1024} # 聚类中心数
}

collection.create_index(
    field_name="embedding",
    index_params=index_params
)

print("✅ 索引创建成功！")
```

**常用索引类型对比：**

| 索引类型 | 速度 | 精度 | 内存占用 | 适用场景 |
|---------|------|------|---------|---------|
| FLAT | 慢 | 最高 | 高 | 小数据集（<10万） |
| IVF_FLAT | 中 | 高 | 中 | 中等数据集（10万-100万） |
| IVF_SQ8 | 快 | 中 | 低 | 大数据集，内存受限 |
| HNSW | 最快 | 高 | 高 | 大数据集，追求速度 |

### 2️⃣ 插入数据

```python
# 准备数据
data = [
    ["paper_001", "paper_002", "paper_003"],  # paper_id
    [
        [0.1] * 768,  # 论文1的768维向量
        [0.2] * 768,  # 论文2的768维向量
        [0.3] * 768,  # 论文3的768维向量
    ],  # embedding
    ["深度学习入门", "机器学习实战", "神经网络原理"],  # title
    ["这是论文1的摘要", "这是论文2的摘要", "这是论文3的摘要"],  # abstract
]

# 插入数据
collection.insert(data)

# 刷新数据到磁盘
collection.flush()

print("✅ 数据插入成功！")
```

### 3️⃣ 搜索相似向量

```python
# 加载集合到内存
collection.load()

# 查询向量
query_vector = [[0.15] * 768]

# 搜索参数
search_params = {
    "metric_type": "L2",
    "params": {"nprobe": 10}  # 搜索的聚类中心数
}

# 执行搜索
results = collection.search(
    data=query_vector,
    anns_field="embedding",
    param=search_params,
    limit=10,  # 返回最相似的10个结果
    output_fields=["paper_id", "title", "abstract"]
)

# 打印结果
for hits in results:
    for hit in hits:
        print(f"论文ID: {hit.entity.get('paper_id')}")
        print(f"标题: {hit.entity.get('title')}")
        print(f"相似度分数: {hit.distance}")
        print("-" * 50)
```

### 4️⃣ 删除数据

```python
# 根据表达式删除
expr = "paper_id in ['paper_001', 'paper_002']"
collection.delete(expr)

print("✅ 数据删除成功！")
```

### 5️⃣ 查询数据

```python
# 根据条件查询（不涉及向量搜索）
expr = "paper_id == 'paper_001'"
results = collection.query(
    expr=expr,
    output_fields=["paper_id", "title", "abstract"]
)

for result in results:
    print(result)
```

## 向量嵌入生成

### 使用 Sentence-Transformers

```python
from sentence_transformers import SentenceTransformer

# 加载模型（首次会下载）
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 生成向量
texts = [
    "深度学习是机器学习的一个分支",
    "神经网络模拟人脑的工作方式",
    "自然语言处理用于理解人类语言"
]

embeddings = model.encode(texts)

print(f"向量维度: {embeddings.shape}")  # (3, 384)
print(f"第一个向量: {embeddings[0][:5]}...")  # 显示前5个值
```

### 使用 OpenAI Embeddings

```python
import openai

openai.api_key = "your-api-key"

def get_embedding(text, model="text-embedding-ada-002"):
    response = openai.Embedding.create(
        input=text,
        model=model
    )
    return response['data'][0]['embedding']

# 生成向量
text = "这是一篇关于深度学习的论文"
embedding = get_embedding(text)

print(f"向量维度: {len(embedding)}")  # 1536
```

## 实战示例

### 完整的论文检索系统

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
from sentence_transformers import SentenceTransformer

class PaperSearchEngine:
    """论文向量检索引擎"""
    
    def __init__(self, host="localhost", port="19530"):
        # 连接 Milvus
        connections.connect(host=host, port=port)
        
        # 加载文本嵌入模型
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # 创建或加载集合
        self.collection_name = "research_papers"
        self._init_collection()
    
    def _init_collection(self):
        """初始化集合"""
        from pymilvus import utility
        
        # 如果集合已存在，直接加载
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            print(f"✅ 集合 '{self.collection_name}' 已加载")
            return
        
        # 定义 schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="paper_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="abstract", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="authors", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="year", dtype=DataType.INT64),
        ]
        
        schema = CollectionSchema(fields, description="研究论文集合")
        self.collection = Collection(self.collection_name, schema)
        
        # 创建索引
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        self.collection.create_index("embedding", index_params)
        
        print(f"✅ 集合 '{self.collection_name}' 创建成功")
    
    def add_papers(self, papers):
        """
        添加论文
        
        Args:
            papers: 论文列表，每个论文是一个字典:
                {
                    'paper_id': 'xxx',
                    'title': 'xxx',
                    'abstract': 'xxx',
                    'authors': 'xxx',
                    'year': 2024
                }
        """
        if not papers:
            return
        
        # 提取文本并生成向量
        texts = [f"{p['title']} {p['abstract']}" for p in papers]
        embeddings = self.model.encode(texts).tolist()
        
        # 准备数据
        data = [
            [p['paper_id'] for p in papers],
            embeddings,
            [p['title'] for p in papers],
            [p['abstract'] for p in papers],
            [p['authors'] for p in papers],
            [p['year'] for p in papers],
        ]
        
        # 插入数据
        self.collection.insert(data)
        self.collection.flush()
        
        print(f"✅ 已添加 {len(papers)} 篇论文")
    
    def search(self, query, top_k=10, year_filter=None):
        """
        搜索相似论文
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            year_filter: 年份过滤，例如 "year >= 2020"
        
        Returns:
            搜索结果列表
        """
        # 加载集合
        self.collection.load()
        
        # 生成查询向量
        query_embedding = self.model.encode([query]).tolist()
        
        # 搜索参数
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        
        # 执行搜索
        results = self.collection.search(
            data=query_embedding,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=year_filter,  # 可选的过滤条件
            output_fields=["paper_id", "title", "abstract", "authors", "year"]
        )
        
        # 格式化结果
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    'paper_id': hit.entity.get('paper_id'),
                    'title': hit.entity.get('title'),
                    'abstract': hit.entity.get('abstract'),
                    'authors': hit.entity.get('authors'),
                    'year': hit.entity.get('year'),
                    'score': hit.distance,
                })
        
        return formatted_results
    
    def delete_papers(self, paper_ids):
        """删除论文"""
        expr = f"paper_id in {paper_ids}"
        self.collection.delete(expr)
        print(f"✅ 已删除 {len(paper_ids)} 篇论文")
    
    def get_stats(self):
        """获取统计信息"""
        self.collection.flush()
        num_entities = self.collection.num_entities
        return {
            'collection_name': self.collection_name,
            'num_papers': num_entities,
        }


# 使用示例
if __name__ == "__main__":
    # 创建检索引擎
    engine = PaperSearchEngine()
    
    # 添加论文
    papers = [
        {
            'paper_id': 'paper_001',
            'title': '深度学习在自然语言处理中的应用',
            'abstract': '本文介绍了深度学习技术在NLP领域的最新进展...',
            'authors': '张三, 李四',
            'year': 2023
        },
        {
            'paper_id': 'paper_002',
            'title': 'Transformer模型综述',
            'abstract': 'Transformer是一种基于注意力机制的神经网络架构...',
            'authors': '王五, 赵六',
            'year': 2024
        },
    ]
    
    engine.add_papers(papers)
    
    # 搜索相似论文
    query = "深度学习和自然语言处理"
    results = engine.search(query, top_k=5)
    
    print("\n🔍 搜索结果：")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   作者: {result['authors']}")
        print(f"   年份: {result['year']}")
        print(f"   相似度分数: {result['score']:.4f}")
        print(f"   摘要: {result['abstract'][:100]}...")
    
    # 获取统计信息
    stats = engine.get_stats()
    print(f"\n📊 统计信息: {stats}")
```

## 最佳实践

### 1. 选择合适的向量维度

| 模型 | 维度 | 语言 | 性能 | 推荐场景 |
|------|------|------|------|---------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 多语言 | 快 | 通用场景 |
| `all-MiniLM-L6-v2` | 384 | 英文 | 快 | 英文文本 |
| `text-embedding-ada-002` (OpenAI) | 1536 | 多语言 | 高质量 | 高精度需求 |
| `bge-large-zh-v1.5` | 1024 | 中文 | 高 | 中文专用 |

### 2. 批量操作

```python
# ❌ 不推荐：逐条插入
for paper in papers:
    collection.insert([paper])

# ✅ 推荐：批量插入
batch_size = 1000
for i in range(0, len(papers), batch_size):
    batch = papers[i:i+batch_size]
    collection.insert(batch)
```

### 3. 搜索参数调优

```python
# nprobe 越大，精度越高，但速度越慢
search_params = {
    "metric_type": "L2",
    "params": {
        "nprobe": 10  # 建议值：10-100
    }
}

# 对于不同的数据规模：
# - 小数据集（<10万）: nprobe=10
# - 中等数据集（10万-100万）: nprobe=20
# - 大数据集（>100万）: nprobe=50
```

### 4. 使用过滤条件

```python
# 组合向量搜索和条件过滤
results = collection.search(
    data=query_vector,
    anns_field="embedding",
    param=search_params,
    limit=10,
    expr="year >= 2020 and year <= 2024",  # 过滤2020-2024年的论文
    output_fields=["title", "year"]
)
```

### 5. 距离度量选择

```python
# L2（欧氏距离）- 适合大多数场景
# 距离越小，越相似
index_params = {"metric_type": "L2", ...}

# IP（内积）- 向量已归一化时使用
# 分数越大，越相似
index_params = {"metric_type": "IP", ...}

# COSINE（余弦相似度）- Milvus 2.3+
# 自动归一化，适合文本向量
index_params = {"metric_type": "COSINE", ...}
```

### 6. 内存管理

```python
# 使用完后释放内存
collection.release()

# 需要时再加载
collection.load()
```

## 常见问题

### Q1: 向量维度必须一致吗？
**A:** 是的！集合创建后，所有插入的向量维度必须与定义的维度一致。

### Q2: 如何更新已有数据？
**A:** Milvus 不支持直接更新，需要先删除再插入：
```python
# 删除旧数据
collection.delete(f"paper_id == '{paper_id}'")
# 插入新数据
collection.insert(new_data)
```

### Q3: 如何备份数据？
**A:** 
1. 导出数据到文件
2. 备份 milvus_data 目录
3. 使用 Milvus 的备份工具

### Q4: 搜索很慢怎么办？
**A:** 
1. 确保已创建索引
2. 调整 nprobe 参数（降低以提速）
3. 使用更快的索引类型（如 IVF_SQ8、HNSW）
4. 增加硬件资源

## 相关资源

- 📚 [Milvus 官方文档](https://milvus.io/docs)
- 🐍 [PyMilvus SDK](https://github.com/milvus-io/pymilvus)
- 🤗 [Sentence Transformers](https://www.sbert.net/)
- 🎯 [向量数据库最佳实践](https://milvus.io/docs/performance_faq.md)

---

**下一步**: 查看 [MILVUS_SETUP.md](./MILVUS_SETUP.md) 了解部署细节

