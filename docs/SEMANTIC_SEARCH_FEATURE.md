# Paper Library 语义搜索功能

## 功能概述

Paper Library 现在支持**基于向量的语义搜索**，可以通过自然语言查询找到相关的论文片段，而不仅仅是关键词匹配。

## 功能特性

### ✨ 核心功能

1. **语义理解** - 理解查询的含义，而不是简单的关键词匹配
2. **段落级检索** - 精确定位到相关的论文段落（chunk）
3. **相关性排序** - 按相关性分数排序结果
4. **实时搜索** - 毫秒级响应速度
5. **高亮显示** - 关键词高亮显示
6. **引用复制** - 一键复制引用格式

### 🎯 搜索模式

#### 1. 简单搜索（默认）
- 按文件名匹配
- 快速过滤
- 适合已知文件名

#### 2. AI 搜索（语义搜索）
- 向量相似度匹配
- 理解查询意图
- 找到语义相关内容

## 使用方法

### 1. 基础搜索

```
1. 在搜索框输入查询
2. 按 Enter 或点击搜索按钮
3. 查看搜索结果
```

### 2. 切换搜索模式

```
1. 点击 "AI Search" 开关
2. 启用后自动使用语义搜索
3. 再次点击切换回简单搜索
```

### 3. 查看结果

每个搜索结果显示：
- 📄 **文件名** - 原始PDF文件名
- 📖 **页码范围** - Chunk所在页码
- ⭐ **相关性分数** - 0-100%，越高越相关
- 📝 **内容预览** - Chunk文本内容（关键词高亮）

### 4. 操作结果

- **View Paper** - 查看完整论文（跳转到对应页码）
- **Copy Citation** - 复制引用格式

## API 接口

### 后端 API

#### POST `/api/papers/search`

**请求：**
```json
{
  "query": "What is transformer architecture?",
  "top_k": 10,
  "uploaded_after": "2026-01-01T00:00:00Z"  // 可选
}
```

**响应：**
```json
{
  "query": "What is transformer architecture?",
  "results": [
    {
      "id": 123456,
      "distance": 0.234,
      "relevance_score": 0.810,
      "paper_id": "20260120_paper.pdf",
      "title": "Attention Is All You Need",
      "file_name": "transformer_paper.pdf",
      "upload_time": "2026-01-20T14:32:17Z",
      "chunk_id": "20260120_paper.pdf#chunk_3",
      "chunk_index": 3,
      "content": "The Transformer model architecture...",
      "chunk_chars": 987,
      "page_range": "2-4",
      "source": "chunk"
    }
  ],
  "total": 10,
  "search_time_ms": 234.56
}
```

### 前端 API

```javascript
import { semanticSearch } from '../api/search'

// 执行搜索
const response = await semanticSearch(
  'transformer architecture',  // 查询
  10,                          // top_k
  null                         // uploaded_after（可选）
)

console.log(response.results)  // 搜索结果
console.log(response.total)    // 结果数量
console.log(response.search_time_ms)  // 搜索耗时
```

## 搜索示例

### 示例 1：技术概念

**查询：** "How does attention mechanism work?"

**结果：**
- 找到所有讨论注意力机制的论文片段
- 按相关性排序
- 高亮关键词 "attention", "mechanism"

### 示例 2：方法比较

**查询：** "Compare RNN and Transformer"

**结果：**
- 找到比较 RNN 和 Transformer 的内容
- 可能来自不同论文
- 按相关性展示

### 示例 3：应用场景

**查询：** "Applications of deep learning in NLP"

**结果：**
- 找到深度学习在 NLP 中的应用案例
- 包含相关的实验结果和讨论

## 工作原理

### 1. 索引阶段（上传时）

```
PDF上传
  ↓
提取文本（50页）
  ↓
切分成chunks（1000字符）
  ↓
生成嵌入向量（OpenAI）
  ↓
存储到Milvus（含metadata）
```

### 2. 搜索阶段（查询时）

```
用户查询
  ↓
生成查询向量（OpenAI）
  ↓
向量相似度检索（Milvus）
  ↓
返回top-k结果（含metadata）
  ↓
前端展示（高亮、排序）
```

### 3. 相关性计算

```python
# 距离转换为相关性分数
relevance_score = 1 / (1 + distance)

# 距离越小，相关性越高
# distance = 0 → relevance = 1.0 (100%)
# distance = 1 → relevance = 0.5 (50%)
# distance = 4 → relevance = 0.2 (20%)
```

## 性能指标

### 搜索速度

| 操作 | 时间 | 说明 |
|------|------|------|
| 生成查询向量 | ~200ms | OpenAI API |
| Milvus检索 | ~50ms | 向量相似度搜索 |
| 结果格式化 | ~10ms | 后端处理 |
| **总计** | **~260ms** | 端到端延迟 |

### 搜索质量

- **召回率** - 能找到相关内容的比例
- **准确率** - 返回结果的相关性
- **排序质量** - 最相关的结果排在前面

### API 成本

- **每次搜索** - ~$0.00002（生成查询向量）
- **1000次搜索** - ~$0.02
- 非常经济实惠！

## 高级功能

### 1. 按论文分组

```javascript
import { groupResultsByPaper } from '../api/search'

const grouped = groupResultsByPaper(results)
// 按paper_id分组，显示每篇论文的相关片段
```

### 2. 去重

```javascript
import { deduplicateResults } from '../api/search'

const deduplicated = deduplicateResults(results, 3)
// 每篇论文最多保留3个chunks
```

### 3. 时间过滤

```javascript
// 只搜索最近7天上传的论文
const sevenDaysAgo = new Date()
sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)

const response = await semanticSearch(
  query,
  10,
  sevenDaysAgo.toISOString()
)
```

### 4. 自定义高亮

```javascript
import { highlightQuery } from '../api/search'

const highlighted = highlightQuery(content, query)
// 返回带<mark>标签的HTML
```

## UI 组件

### 搜索框

```vue
<div class="search-box">
  <input 
    v-model="searchQuery"
    @keyup.enter="handleSemanticSearch"
    placeholder="Search papers..."
  />
  <button @click="handleSemanticSearch">
    Search
  </button>
</div>
```

### 搜索结果卡片

```vue
<div class="search-result-card">
  <div class="result-header">
    <h4>{{ result.title }}</h4>
    <span class="relevance-badge">
      ⭐ {{ formatRelevance(result.relevance_score) }}
    </span>
  </div>
  <div class="result-content" v-html="highlightContent(result.content)">
  </div>
  <div class="result-actions">
    <button @click="viewPaper(result)">View Paper</button>
    <button @click="copyReference(result)">Copy Citation</button>
  </div>
</div>
```

## 样式定制

### 相关性颜色

```css
.relevance-badge.high {
  background: rgba(0, 255, 136, 0.2);  /* 绿色：80-100% */
  color: var(--accent-success);
}

.relevance-badge.medium {
  background: rgba(255, 193, 7, 0.2);  /* 黄色：60-80% */
  color: #ffc107;
}

.relevance-badge.low {
  background: rgba(255, 255, 255, 0.1);  /* 灰色：<60% */
  color: var(--text-secondary);
}
```

### 高亮样式

```css
.result-content mark {
  background: rgba(255, 193, 7, 0.3);
  color: #ffc107;
  padding: 2px 4px;
  border-radius: 2px;
}
```

## 故障排查

### 问题 1：搜索无结果

**原因：**
- 论文库为空
- 查询太具体
- Milvus未连接

**解决：**
```bash
# 检查Milvus
docker-compose ps milvus-standalone

# 检查论文数量
curl http://localhost:8000/api/papers/list
```

### 问题 2：搜索很慢

**原因：**
- OpenAI API延迟
- Milvus索引未优化
- 网络问题

**解决：**
```python
# 优化Milvus索引
milvus_service.create_index(
    index_type="HNSW",  # 更快的索引
    metric_type="COSINE"
)
```

### 问题 3：相关性低

**原因：**
- 查询太模糊
- 论文内容不相关
- 嵌入质量问题

**解决：**
- 使用更具体的查询
- 尝试不同的关键词
- 检查论文是否相关

## 未来改进

### 短期（1-2周）
- [ ] 搜索历史记录
- [ ] 保存常用查询
- [ ] 导出搜索结果

### 中期（1-2个月）
- [ ] 混合检索（BM25 + 向量）
- [ ] 结果重排序
- [ ] 多轮对话搜索
- [ ] 搜索建议

### 长期（3-6个月）
- [ ] 个性化搜索
- [ ] 协作式标注
- [ ] 搜索分析
- [ ] A/B测试

## 相关文档

- [Chunk-Based RAG 系统](./CHUNK_BASED_RAG.md)
- [Metadata 使用指南](./METADATA_IN_MILVUS.md)
- [Milvus 设置](./MILVUS_SETUP.md)

## 总结

语义搜索功能让 Paper Library 更加智能：

✅ **理解意图** - 不只是关键词匹配  
✅ **精确定位** - 段落级别的检索  
✅ **快速响应** - 毫秒级搜索速度  
✅ **丰富信息** - 完整的metadata  
✅ **用户友好** - 直观的UI设计  

现在就开始使用语义搜索，发现论文中的知识！🔍

