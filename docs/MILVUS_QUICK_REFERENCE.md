# Milvus 快速参考手册

## 🚀 5分钟快速上手

### 1. 启动服务
```bash
docker-compose up -d
```

### 2. 访问管理界面
打开浏览器：http://localhost:9002
连接地址：`localhost:19530`

### 3. 运行示例
```bash
cd backend
python examples/quick_start_milvus.py
```

## 📝 常用代码片段

### 连接 Milvus
```python
from pymilvus import connections

connections.connect(host="localhost", port="19530")
```

### 创建集合
```python
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=1000),
]

schema = CollectionSchema(fields, description="我的集合")
collection = Collection(name="my_collection", schema=schema)
```

### 创建索引
```python
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}
}

collection.create_index("embedding", index_params)
```

### 插入数据
```python
data = [
    [[0.1] * 768, [0.2] * 768],  # embeddings
    ["文本1", "文本2"],            # text
]

collection.insert(data)
collection.flush()
```

### 搜索
```python
collection.load()

query_vector = [[0.15] * 768]
search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

results = collection.search(
    data=query_vector,
    anns_field="embedding",
    param=search_params,
    limit=10,
    output_fields=["text"]
)

for hits in results:
    for hit in hits:
        print(f"文本: {hit.entity.get('text')}, 距离: {hit.distance}")
```

### 删除数据
```python
expr = "id in [1, 2, 3]"
collection.delete(expr)
```

## 🎯 使用项目封装的服务

```python
from app.services.milvus_service import milvus_service

# 连接
milvus_service.connect()

# 创建集合
milvus_service.create_collection(dim=768)

# 创建索引
milvus_service.create_index()

# 插入向量
milvus_service.insert_vectors(
    paper_ids=["paper_001"],
    embeddings=[[0.1] * 768],
    titles=["论文标题"],
    abstracts=["论文摘要"],
    sources=["abstract"]
)

# 搜索
results = milvus_service.search_similar(
    query_vectors=[[0.1] * 768],
    top_k=10
)
```

## 📊 索引类型选择

| 场景 | 推荐索引 | 参数 |
|------|---------|------|
| 数据量 < 10万 | FLAT | - |
| 数据量 10万-100万 | IVF_FLAT | nlist=1024 |
| 需要节省内存 | IVF_SQ8 | nlist=1024 |
| 追求极致速度 | HNSW | M=16, efConstruction=200 |

## 🔧 距离度量

| 度量类型 | 说明 | 使用场景 |
|---------|------|---------|
| L2 | 欧氏距离 | 通用场景 |
| IP | 内积 | 归一化向量 |
| COSINE | 余弦相似度 | 文本向量（Milvus 2.3+） |

## ⚡ 性能优化

### 批量操作
```python
# ❌ 慢
for item in items:
    collection.insert([item])

# ✅ 快
collection.insert(items)
```

### 调整搜索参数
```python
# 更快，但精度稍低
search_params = {"metric_type": "L2", "params": {"nprobe": 5}}

# 更准确，但速度稍慢
search_params = {"metric_type": "L2", "params": {"nprobe": 50}}
```

### 释放内存
```python
collection.release()  # 不用时释放
collection.load()     # 需要时加载
```

## 🛠️ 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看 Milvus 日志
docker-compose logs milvus

# 重启 Milvus
docker-compose restart milvus

# 停止所有服务
docker-compose down

# 停止并删除数据（谨慎！）
docker-compose down -v
```

## 🔗 服务地址

| 服务 | 地址 | 用途 |
|------|------|------|
| Milvus | localhost:19530 | gRPC 连接 |
| Attu | http://localhost:9002 | Web 管理界面 |
| Milvus Metrics | http://localhost:9091 | 监控指标 |
| MinIO Console | http://localhost:9001 | 对象存储管理 |

## 📚 文档链接

- [完整使用指南](./MILVUS_USAGE.md)
- [部署文档](./MILVUS_SETUP.md)
- [快速开始](./QUICK_START.md)
- [Milvus 官方文档](https://milvus.io/docs)

## 🐛 常见问题

### Q: 连接失败
```bash
# 检查服务是否启动
docker-compose ps

# 查看日志
docker-compose logs milvus
```

### Q: 搜索很慢
```python
# 1. 确保创建了索引
collection.create_index(...)

# 2. 降低 nprobe
search_params = {"params": {"nprobe": 10}}

# 3. 使用更快的索引
index_params = {"index_type": "IVF_SQ8", ...}
```

### Q: 内存不足
```python
# 使用完后释放内存
collection.release()

# 使用压缩索引
index_params = {"index_type": "IVF_SQ8", ...}
```

---

**提示**: 这是快速参考手册。详细说明请查看 [MILVUS_USAGE.md](./MILVUS_USAGE.md)

