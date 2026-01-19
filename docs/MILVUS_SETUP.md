# Milvus 向量数据库部署指南

## 服务概览

本项目已配置以下服务：

1. **Milvus** - 向量数据库
2. **Attu** - Milvus 可视化管理界面
3. **etcd** - Milvus 元数据存储
4. **MinIO** - 对象存储（Milvus 数据存储后端）

## 端口映射

| 服务 | 端口 | 说明 |
|------|------|------|
| Milvus gRPC | 19530 | Milvus 数据库连接端口 |
| Milvus Metrics | 9091 | Prometheus 监控指标 |
| Attu Web UI | 9002 | 可视化管理界面 |
| MinIO API | 9000 | MinIO 对象存储 API |
| MinIO Console | 9001 | MinIO 控制台 |

## 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看 Milvus 日志
docker-compose logs -f milvus
```

## 访问 Attu 可视化界面

1. 启动服务后，打开浏览器访问：`http://localhost:9002`
2. 在连接页面输入：
   - **Milvus Address**: `milvus:19530`（或者使用 `localhost:19530`）
   - 点击 "Connect" 连接

## 使用 Python SDK 连接 Milvus

### 安装 SDK

```bash
pip install pymilvus
```

### 连接示例

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# 连接到 Milvus
connections.connect(
    alias="default",
    host="localhost",
    port="19530"
)

# 定义 Collection Schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
]
schema = CollectionSchema(fields, description="论文向量集合")

# 创建 Collection
collection = Collection(name="papers", schema=schema)

# 创建索引
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}
}
collection.create_index(field_name="embedding", index_params=index_params)

# 插入数据
entities = [
    [1.0] * 768,  # embedding 向量
    ["这是一篇论文的摘要"],  # text
]
collection.insert(entities)

# 加载 Collection 到内存
collection.load()

# 搜索相似向量
search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
results = collection.search(
    data=[[1.0] * 768],  # 查询向量
    anns_field="embedding",
    param=search_params,
    limit=10
)
```

## 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止服务并删除数据卷（谨慎使用！）
docker-compose down -v
```

## 数据持久化

数据存储在以下目录：
- `./milvus_data` - Milvus 数据
- `./etcd_data` - etcd 元数据
- `./minio_data` - MinIO 对象存储

## 常见问题

### 1. 服务启动失败

检查端口是否被占用：
```bash
netstat -ano | findstr "19530"
netstat -ano | findstr "8000"
```

### 2. 连接超时

确保所有依赖服务都已启动：
```bash
docker-compose ps
```

等待健康检查通过：
```bash
docker-compose logs milvus | grep "health"
```

### 3. 内存不足

Milvus 需要至少 4GB 可用内存。可以在 docker-compose.yml 中添加资源限制：

```yaml
milvus:
  deploy:
    resources:
      limits:
        memory: 4G
      reservations:
        memory: 2G
```

## 性能优化建议

1. **索引选择**：
   - `IVF_FLAT`：精度高，速度中等
   - `IVF_SQ8`：内存占用小，速度快
   - `HNSW`：查询速度最快，内存占用大

2. **距离度量**：
   - `L2`：欧氏距离
   - `IP`：内积（用于归一化向量）
   - `COSINE`：余弦相似度

3. **批量操作**：
   - 批量插入数据可以提高性能
   - 建议每批 1000-10000 条记录

## 参考资料

- [Milvus 官方文档](https://milvus.io/docs)
- [Attu GitHub](https://github.com/zilliz/attu)
- [PyMilvus 文档](https://milvus.io/docs/install-pymilvus.md)

