# Milvus 管理页面使用指南

## 🎯 访问方式

启动前后端服务后，访问：http://localhost:5173/milvus

或者在左侧导航栏点击 **Milvus Manager** 图标。

## 📊 功能概览

### 1. 连接状态监控

页面顶部显示：
- ✅ **Connected** - Milvus 连接正常
- ❌ **Disconnected** - Milvus 未连接

点击刷新按钮可以重新检查连接状态。

### 2. 统计概览

三个统计卡片显示：
- **Collections**: 集合总数
- **Total Vectors**: 所有集合的向量总数
- **Loaded**: 已加载到内存的集合数

### 3. 集合管理

#### 创建集合
1. 点击 **Create Collection** 按钮
2. 填写信息：
   - **Collection Name**: 集合名称（必填）
   - **Description**: 描述（可选）
   - **Vector Dimension**: 向量维度（必填）
     - 384: MiniLM 模型
     - 768: BERT 模型
     - 1536: OpenAI 模型
3. 点击 **Create Collection**

#### 查看集合
每个集合卡片显示：
- 📁 集合名称和描述
- 📊 统计信息：
  - Vectors: 向量数量
  - Dimension: 向量维度
  - Index: 索引类型
- ✅ Loaded 标记（如果已加载）

#### 集合操作
- **Load**: 加载集合到内存（搜索前必须加载）
- **Release**: 从内存释放集合（节省内存）
- **View**: 查看集合详细信息
- **Delete**: 删除集合（⚠️ 谨慎操作！）

### 4. 搜索和筛选

使用搜索框可以：
- 根据集合名称搜索
- 根据描述搜索
- 实时过滤结果

## 🎨 界面特点

### 视觉效果
- 🌌 深色科技风格
- 💫 渐变和光效
- ✨ 流畅动画过渡
- 🎯 清晰的状态指示

### 状态标识
- **绿色边框** - 已加载的集合
- **蓝色高亮** - hover 效果
- **红色按钮** - 危险操作（删除）
- **脉冲动画** - 连接状态指示器

## 📝 使用场景

### 场景 1: 首次使用
```
1. 访问 /milvus 页面
2. 检查连接状态（应该显示 Connected）
3. 创建第一个集合
4. 加载集合到内存
5. 开始使用向量搜索功能
```

### 场景 2: 日常管理
```
1. 查看所有集合及其状态
2. 根据需要 Load/Release 集合
3. 监控向量数量变化
4. 清理不需要的集合
```

### 场景 3: 性能优化
```
1. Release 不常用的集合
2. 只 Load 需要搜索的集合
3. 通过统计信息监控内存使用
```

## ⚠️ 重要提示

### 删除集合
- ❌ **删除操作不可恢复**
- 🗑️ 会删除集合中的所有向量数据
- ⚡ 删除前会显示确认对话框
- 📊 显示将要删除的向量数量

### Load/Release
- 🔄 **Load**: 必须先加载集合才能搜索
- 💾 **Release**: 释放内存但不删除数据
- ⚡ 加载大集合可能需要时间
- 📊 已加载的集合会显示绿色标记

### 性能建议
- 📈 不要同时加载过多大集合
- 🎯 只加载当前需要的集合
- 💾 定期 Release 不用的集合
- 📊 监控统计信息保持系统性能

## 🔧 故障排查

### 问题 1: 显示 Disconnected
**解决方案**:
```bash
# 1. 检查 Milvus 服务是否运行
docker-compose ps milvus

# 2. 查看 Milvus 日志
docker-compose logs milvus

# 3. 重启 Milvus
docker-compose restart milvus
```

### 问题 2: 无法创建集合
**可能原因**:
- 集合名称已存在
- 向量维度无效
- Milvus 未连接

**解决方案**:
- 检查集合名称是否重复
- 使用常见维度值（384, 768, 1536）
- 确认连接状态

### 问题 3: Load 失败
**可能原因**:
- 内存不足
- 集合损坏
- Milvus 服务异常

**解决方案**:
```bash
# 检查 Docker 内存分配
docker stats

# 查看详细错误日志
docker-compose logs milvus --tail 50

# 重启服务
docker-compose restart milvus
```

## 🎓 最佳实践

### 1. 命名规范
```
✅ 好的命名:
- research_papers
- user_embeddings_768d
- doc_vectors_v2

❌ 避免:
- test
- temp
- 123
```

### 2. 描述规范
```
✅ 清晰的描述:
"Research paper abstracts with 768D BERT embeddings"
"User profile vectors using OpenAI ada-002 model"

❌ 模糊的描述:
"test collection"
"vectors"
```

### 3. 维度选择
```
📊 根据你的模型选择:
- sentence-transformers/paraphrase-MiniLM-L12-v2: 384
- bert-base-uncased: 768
- text-embedding-ada-002 (OpenAI): 1536
- bge-large-zh-v1.5 (中文): 1024
```

### 4. 内存管理
```
策略:
1. 只加载活跃使用的集合
2. 搜索完成后及时 Release
3. 定期检查统计信息
4. 清理不用的集合
```

## 🔗 相关资源

- [Milvus 使用指南](./MILVUS_USAGE.md)
- [Milvus 快速参考](./MILVUS_QUICK_REFERENCE.md)
- [Milvus 部署文档](./MILVUS_SETUP.md)
- [Attu 可视化工具](http://localhost:9002)

## 📞 技术支持

遇到问题？
1. 查看 [常见问题](./MILVUS_USAGE.md#常见问题)
2. 检查 [Milvus 日志](../docker-compose.yml)
3. 访问 [Milvus 官方文档](https://milvus.io/docs)

---

**提示**: Milvus Manager 提供友好的 Web 界面，Attu 提供更专业的管理功能。根据需要选择使用。

