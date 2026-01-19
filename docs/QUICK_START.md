# Milvus 快速启动指南

## 🚀 一键启动

### 1. 启动所有服务

```bash
docker-compose up -d
```

这将启动以下服务：
- ✅ **MinIO** - 对象存储 (端口: 9000, 9001)
- ✅ **etcd** - 元数据存储
- ✅ **Milvus** - 向量数据库 (端口: 19530, 9091)
- ✅ **Attu** - 可视化管理界面 (端口: 8000)

### 2. 检查服务状态

```bash
docker-compose ps
```

等待所有服务的状态变为 `healthy` 或 `running`。

### 3. 访问 Attu 可视化界面

1. 打开浏览器访问：http://localhost:9002
2. 在连接页面输入 Milvus 地址：`milvus:19530`
3. 点击 "Connect" 连接

## 📊 访问地址汇总

| 服务 | 地址 | 说明 |
|------|------|------|
| Attu 管理界面 | http://localhost:9002 | Milvus 可视化管理 |
| MinIO 控制台 | http://localhost:9001 | 对象存储管理 |
| Milvus gRPC | localhost:19530 | 数据库连接地址 |
| Milvus Metrics | http://localhost:9091 | Prometheus 监控 |

## 🔧 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

## 💻 运行示例程序

```bash
cd backend
python examples/milvus_example.py
```

该示例将演示：
- ✅ 连接到 Milvus
- ✅ 创建向量集合
- ✅ 插入向量数据
- ✅ 搜索相似向量
- ✅ 删除数据

## 📝 在代码中使用 Milvus

### 基本用法

```python
from app.services.milvus_service import milvus_service

# 1. 连接
milvus_service.connect()

# 2. 创建集合
milvus_service.create_collection(dim=768)

# 3. 创建索引
milvus_service.create_index()

# 4. 插入数据
milvus_service.insert_vectors(
    paper_ids=["paper_001"],
    embeddings=[[0.1, 0.2, ...]],  # 768维向量
    titles=["论文标题"],
    abstracts=["论文摘要"],
    sources=["abstract"]
)

# 5. 搜索相似向量
results = milvus_service.search_similar(
    query_vectors=[[0.1, 0.2, ...]],
    top_k=10
)
```

## 🛑 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据（谨慎使用！）
docker-compose down -v
```

## 📦 数据存储位置

数据持久化在以下目录：
```
./minio_data/   # MinIO 对象存储数据
./etcd_data/    # etcd 元数据
./milvus_data/  # Milvus 向量数据
```

## ⚠️ 常见问题

### 服务启动失败

1. **端口被占用**
   ```bash
   # Windows
   netstat -ano | findstr "19530"
   netstat -ano | findstr "9002"
   
   # Linux/Mac
   lsof -i :19530
   lsof -i :9002
   ```

2. **内存不足**
   - Milvus 至少需要 4GB 可用内存
   - 可以在 Docker Desktop 中增加内存限制

3. **etcd 健康检查失败**
   ```bash
   # 查看 etcd 日志
   docker-compose logs etcd
   ```

### 连接超时

确保服务已完全启动：
```bash
# 查看 Milvus 日志
docker-compose logs -f milvus

# 等待出现 "Milvus Proxy successfully started"
```

## 📚 更多文档

- [详细部署指南](./MILVUS_SETUP.md)
- [环境变量配置](./ENV_CONFIG.md)
- [Milvus 官方文档](https://milvus.io/docs)

## 🎯 下一步

1. ✅ 启动服务
2. ✅ 访问 Attu 界面
3. ✅ 运行示例程序
4. ✅ 集成到你的应用中

Happy Coding! 🎉

