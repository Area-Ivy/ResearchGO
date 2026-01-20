# Paper Library 上传到 Milvus - 快速开始

## 🚀 快速开始

### 1. 确保服务运行

```bash
# 启动 Milvus 和 MinIO
docker-compose up -d milvus-standalone minio

# 检查服务状态
docker-compose ps
```

### 2. 配置环境变量

编辑 `backend/.env` 文件：

```env
# OpenAI API (必需)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o

# Milvus (默认配置)
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 3. 启动后端

```bash
cd backend
python run.py
```

### 4. 启动前端

```bash
cd frontend
npm run dev
```

### 5. 测试功能

1. 访问 http://localhost:5173
2. 进入 "Paper Library" 页面
3. 上传一个 PDF 文件
4. 查看后端日志，确认成功存储到 Milvus

## ✅ 验证安装

运行测试脚本：

```bash
cd backend
python test_paper_upload_milvus.py
```

预期输出：
```
============================================================
Paper Upload to Milvus - 功能测试
============================================================

=== 测试 Milvus 连接 ===
✓ 成功连接到 Milvus
✓ 集合创建/验证成功
✓ 索引创建成功
✓ 集合统计信息: {...}
✓ 已断开 Milvus 连接

=== 测试 OpenAI 嵌入生成 ===
✓ OpenAI 服务初始化成功
✓ 成功生成 2 个嵌入向量
  - 向量维度: 1536
  - 前5个值: [...]

=== 测试完整工作流程 ===
生成嵌入向量...
✓ 生成嵌入成功，维度: 1536
存储到 Milvus...
✓ 成功存储到 Milvus
✓ 当前集合实体数: 1
测试相似度搜索...
✓ 搜索成功，找到 1 个结果
  1. 标题: Test Paper: Machine Learning Applications
     距离: 0.0000
清理测试数据...
✓ 测试数据已清理

✓ 完整工作流程测试成功！

============================================================
测试总结:
  Milvus 连接测试: ✓ 通过
  OpenAI 嵌入测试: ✓ 通过
  完整工作流程测试: ✓ 通过
============================================================

✓ 所有测试通过！系统已准备好处理论文上传。
```

## 📋 功能说明

### 上传论文时会自动：

1. ✅ 存储 PDF 到 MinIO
2. ✅ 提取 PDF 文本（前3页）
3. ✅ 生成嵌入向量（OpenAI）
4. ✅ 存储到 Milvus 向量数据库

### 删除论文时会自动：

1. ✅ 从 MinIO 删除文件
2. ✅ 从 Milvus 删除向量数据

## 🔧 常见问题

### Q: Milvus 连接失败？
```bash
# 检查服务
docker-compose ps milvus-standalone

# 查看日志
docker-compose logs milvus-standalone

# 重启服务
docker-compose restart milvus-standalone
```

### Q: OpenAI API 错误？
```bash
# 检查 API Key
cat backend/.env | grep OPENAI_API_KEY

# 测试 API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Q: 上传成功但没有存储到 Milvus？
- 检查后端日志：`tail -f backend/logs/app.log`
- Milvus 存储失败不会影响上传成功
- 查看是否有 "Failed to store in Milvus" 的错误日志

### Q: PDF 文本提取失败？
- 确保 PDF 不是扫描版（需要 OCR）
- 检查 PDF 是否损坏
- 查看日志中的具体错误信息

## 📊 查看存储的数据

### 使用 Python 查询

```python
from app.services.milvus_service import MilvusService

# 连接 Milvus
service = MilvusService()
service.connect()

# 获取统计信息
stats = service.get_collection_stats()
print(f"集合中的论文数量: {stats['num_entities']}")

# 断开连接
service.disconnect()
```

### 使用 Attu (Milvus GUI)

1. 访问 http://localhost:8000 (如果已配置)
2. 连接到 localhost:19530
3. 查看 `research_papers` 集合

## 📖 详细文档

- [完整功能文档](docs/PAPER_UPLOAD_MILVUS.md)
- [集成说明](backend/PAPER_MILVUS_INTEGRATION.md)
- [Milvus 设置](docs/MILVUS_SETUP.md)

## 🎯 下一步

现在你可以：

1. 上传论文到 Paper Library
2. 论文会自动存储到 Milvus
3. 为未来的语义搜索功能做准备
4. 实现相似论文推荐功能

## 💡 提示

- Milvus 存储是异步的，不会阻塞上传
- 即使 Milvus 失败，上传仍会成功
- 建议定期备份 Milvus 数据
- 可以通过 Milvus Manager 页面管理向量数据

## 🆘 需要帮助？

查看日志文件：
```bash
# 后端日志
tail -f backend/logs/app.log

# Milvus 日志
docker-compose logs -f milvus-standalone

# 过滤相关日志
tail -f backend/logs/app.log | grep -E "Uploading|Milvus|embedding"
```

