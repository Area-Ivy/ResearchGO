# ResearchGO Agent 记忆架构分析

## 概述

ResearchGO Agent 采用**三层记忆架构**，分别处理短期、中期和长期记忆需求，确保在保持上下文连贯性的同时，有效控制 Token 消耗和存储成本。

## 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    ResearchGO Agent                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           三层记忆架构 (Three-Layer Memory)          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  短期记忆     │  │  中期记忆     │  │  长期记忆     │     │
│  │ Short-term   │  │ Mid-term     │  │ Long-term    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │            │
│    ┌────┴────┐      ┌──────┴──────┐    ┌──────┴──────┐    │
│    │ 滑动窗口 │      │  对话摘要    │    │  语义记忆    │    │
│    │ 窗口    │      │  摘要        │    │  记忆        │    │
│    └─────────┘      └─────────────┘    └─────────────┘    │
│         │                  │                  │            │
│    ┌────┴────┐      ┌──────┴──────┐    ┌──────┴──────┐    │
│    │ Checkpoint│     │  Redis Cache │    │ Vector DB    │    │
│    │ (Redis)  │     │  (Redis)     │    │ (Milvus)     │    │
│    └─────────┘      └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 第一层：短期记忆 (Short-term Memory)

### 1.1 滑动窗口 (Sliding Window)

**目的**：限制单次对话的上下文长度，避免 Token 超限

**实现位置**：`app/memory/sliding_window.py`

**核心组件**：

#### 1.1.1 `SlidingWindowManager` - 简单滑动窗口
- **策略**：按消息数量限制
- **默认窗口大小**：10 轮对话（`SLIDING_WINDOW_SIZE`）
- **保留策略**：
  - 始终保留 system 消息
  - 保留第一条 user 消息（原始意图）
  - 保留最近的 N 轮对话

#### 1.1.2 `TokenAwareSlidingWindow` - Token 感知窗口
- **策略**：精确控制 Token 数量
- **默认最大 Token**：4000（`MAX_CONTEXT_TOKENS`）
- **特性**：
  - 使用 `tiktoken` 精确计算 Token
  - 预留响应 Token（默认 500）
  - 优先保留工具调用结果（priority_roles）

#### 1.1.3 `SmartSlidingWindow` - 智能混合窗口
- **策略**：结合消息数量和 Token 限制
- **工作流程**：
  1. 先用简单窗口粗筛
  2. 再用 Token 窗口精筛
- **优势**：兼顾效率和精确度

**配置参数**：
```python
SLIDING_WINDOW_SIZE = 10          # 保留最近N轮对话
MAX_CONTEXT_TOKENS = 4000         # 最大上下文Token数
ENABLE_TOKEN_COUNTING = true     # 启用Token计数
```

**使用场景**：
- 每次推理前应用，限制输入上下文
- 在对话摘要之后应用，进一步压缩

---

### 1.2 Redis Checkpointer

**目的**：保存和恢复 Agent 状态，支持断点续传

**实现位置**：`app/memory/checkpointer.py`

**核心功能**：

1. **状态持久化**
   - 保存完整的 AgentState（消息、工具调用、迭代次数等）
   - 支持异步和同步操作
   - 自动 TTL 过期（默认 24 小时）

2. **存储结构**：
   ```
   checkpoint:{thread_id}:{checkpoint_id}     -> checkpoint 数据
   checkpoint_meta:{thread_id}:{checkpoint_id} -> 元数据
   checkpoint_latest:{thread_id}              -> 最新 checkpoint_id
   ```

3. **LangGraph 集成**：
   - 实现 `BaseCheckpointSaver` 接口
   - 支持 `aget_tuple`、`aput`、`alist` 等操作
   - 与 LangGraph 的 `compile(checkpointer=...)` 集成

**配置参数**：
```python
ENABLE_CHECKPOINTER = true       # 启用 Checkpointer
CHECKPOINT_TTL = 86400          # 过期时间（秒），默认24小时
REDIS_URL = "redis://..."       # Redis 连接地址
```

**使用场景**：
- 多轮对话中保存中间状态
- 支持对话恢复和回溯
- 跨进程状态共享

---

## 第二层：中期记忆 (Mid-term Memory)

### 2.1 对话摘要 (Conversation Summary)

**目的**：自动摘要超长对话，保留关键信息

**实现位置**：`app/memory/summary.py`

**核心功能**：

1. **自动摘要生成**
   - 当对话超过阈值（默认 20 条消息）时触发
   - 使用 LLM 生成简洁摘要（最多 500 tokens）
   - 摘要包含：用户需求、关键信息、讨论主题

2. **增量更新**
   - 缓存已生成的摘要到 Redis
   - 只对新消息生成增量摘要
   - 合并旧摘要和新消息

3. **存储结构**：
   ```
   summary:{conversation_id}        -> 摘要内容
   summary_meta:{conversation_id}   -> 元数据（消息数、更新时间）
   ```

4. **工作流程**：
   ```
   对话历史 → 检查是否超过阈值
              ↓ 是
           分割消息（旧消息 | 窗口消息）
              ↓
           检查缓存摘要
              ↓
           生成/更新摘要
              ↓
           返回：摘要 + 最近窗口消息
   ```

**配置参数**：
```python
ENABLE_CONVERSATION_SUMMARY = true  # 启用摘要
SUMMARY_THRESHOLD = 20              # 触发阈值（消息数）
SUMMARY_MAX_TOKENS = 500            # 摘要最大Token数
```

**使用场景**：
- 长对话（>20 条消息）自动压缩
- 保留对话核心信息，丢弃细节
- 与滑动窗口配合，双重压缩

---

### 2.2 对话缓存 (Conversation Cache)

**目的**：优化对话历史的读写性能

**实现位置**：`app/memory/conversation_cache.py`

**核心功能**：

1. **缓存策略**：
   - **读取**：Redis 缓存优先，未命中时从 conversation-service 加载
   - **写入**：先更新缓存（同步），再异步持久化到 conversation-service
   - **TTL**：6 小时缓存过期

2. **后台写入队列**：
   - 异步写入 conversation-service，不阻塞响应
   - 使用 `asyncio.Queue` 管理写入任务
   - 支持批量写入优化

3. **存储结构**：
   ```
   conv_history:{conversation_id}  -> JSON 消息列表
   conv_meta:{conversation_id}     -> 元数据
   ```

4. **性能优化**：
   - 热数据在 Redis，毫秒级读取
   - 冷数据从数据库加载，自动缓存
   - 写入异步化，响应速度快

**配置参数**：
```python
REDIS_URL = "redis://..."                    # Redis 连接
CONVERSATION_SERVICE_URL = "http://..."      # 对话服务地址
cache_ttl = 3600 * 6                         # 缓存TTL（6小时）
```

**使用场景**：
- 频繁读取对话历史时加速
- 减少对 conversation-service 的请求压力
- 提升用户体验（快速响应）

---

## 第三层：长期记忆 (Long-term Memory)

### 3.1 语义记忆 (Semantic Memory)

**目的**：跨会话存储用户画像和偏好，支持个性化服务

**实现位置**：`app/memory/semantic_memory.py`

**核心功能**：

1. **记忆提取**
   - 使用 LLM 从对话中提取重要信息
   - 支持 5 种记忆类型：
     - `USER_PREFERENCE`：用户偏好（如：喜欢简洁回答）
     - `RESEARCH_INTEREST`：研究兴趣（如：关注 transformer 领域）
     - `KEY_FINDING`：重要发现（如：找到了有价值的论文）
     - `TASK_CONTEXT`：任务上下文（如：正在写关于 X 的论文）
     - `FEEDBACK`：用户反馈
   - 自动评估重要性（0.0-1.0），过滤低重要性记忆

2. **记忆存储**
   - 存储到向量数据库（Milvus）
   - 复用现有的 `vector-search-service`
   - 使用特殊 `paper_id` 格式：`memory_{user_id}`
   - 支持元数据（重要性、类型、时间戳）

3. **记忆检索**
   - 基于语义相似度检索相关记忆
   - 使用混合检索（向量 + 关键词）
   - 支持重排序（reranker）
   - 返回 Top-K 相关记忆（默认 5 条）

4. **上下文生成**
   - 将检索到的记忆格式化为上下文字符串
   - 按类型分组展示（研究兴趣、偏好、任务等）
   - 注入到 System Prompt 中

5. **工作流程**：
   ```
   对话结束 → 提取记忆（LLM分析）
              ↓
           评估重要性（过滤阈值）
              ↓
           存储到向量数据库
              ↓
   下次对话 → 语义检索相关记忆
              ↓
           格式化上下文
              ↓
           注入 System Prompt
   ```

**配置参数**：
```python
ENABLE_SEMANTIC_MEMORY = true              # 启用语义记忆
SEMANTIC_MEMORY_TOP_K = 5                  # 检索记忆数量
MEMORY_IMPORTANCE_THRESHOLD = 0.7         # 重要性阈值
VECTOR_SEARCH_SERVICE_URL = "http://..."  # 向量服务地址
```

**使用场景**：
- 跨会话记住用户偏好
- 个性化推荐和回答
- 长期用户画像构建

---

## 记忆系统集成流程

### 在 Agent 中的使用

**位置**：`app/agent/graph.py` 的 `_prepare_context` 方法

**执行顺序**：

```python
async def _prepare_context(...):
    # 1. 长对话摘要（如果启用）
    if ENABLE_CONVERSATION_SUMMARY:
        summary_result = await summary_manager.process(...)
        processed_messages = summary_result.window_messages
    
    # 2. 滑动窗口（进一步压缩）
    processed_messages, window_stats = sliding_window.apply(...)
    
    # 3. 语义记忆（获取用户上下文）
    if ENABLE_SEMANTIC_MEMORY:
        memory_context = await semantic_memory.get_user_context(...)
    
    return processed_messages, summary, memory_context
```

**上下文注入**：

```python
# 在 System Prompt 中注入记忆上下文
memory_section = """
--- 上下文信息 ---
[对话摘要]: {summary}
[用户背景]:
{memory_context}
--- 上下文结束 ---
"""
```

**后处理**：

```python
# 对话结束后，异步提取并存储语义记忆
await semantic_memory.process_and_store(
    messages=final_messages,
    user_id=user_id,
    token=token
)
```

---

## 数据流图

```
用户输入
   ↓
┌─────────────────────────────────────┐
│  _prepare_context (准备上下文)      │
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ 1. 对话摘要 (如果 > 20 条消息)      │
│    - 检查缓存                        │
│    - 生成/更新摘要                   │
│    - 返回：摘要 + 窗口消息           │
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ 2. 滑动窗口 (进一步压缩)            │
│    - 简单窗口：按消息数              │
│    - Token窗口：按Token数            │
│    - 保留：system + 第一条user + 最近│
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ 3. 语义记忆 (检索用户上下文)         │
│    - 语义检索相关记忆                │
│    - 格式化上下文                    │
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ 构建最终上下文                       │
│ - System Prompt + 记忆上下文        │
│ - 处理后的消息历史                   │
└─────────────────────────────────────┘
   ↓
LLM 推理
   ↓
┌─────────────────────────────────────┐
│ 后处理：提取语义记忆                 │
│ - LLM 分析对话                      │
│ - 提取重要信息                      │
│ - 存储到向量数据库                   │
└─────────────────────────────────────┘
```

---

## 存储架构

### Redis 存储

```
# Checkpointer
checkpoint:{thread_id}:{checkpoint_id}        # Agent 状态
checkpoint_meta:{thread_id}:{checkpoint_id}    # 元数据
checkpoint_latest:{thread_id}                  # 最新 checkpoint

# 对话摘要
summary:{conversation_id}                      # 摘要内容
summary_meta:{conversation_id}                  # 摘要元数据

# 对话缓存
conv_history:{conversation_id}                 # 消息历史（JSON）
conv_meta:{conversation_id}                    # 对话元数据
```

### Milvus 向量数据库

```
Collection: user_memories
Fields:
  - user_id: str
  - content: str (记忆内容)
  - memory_type: str (记忆类型)
  - importance: float (重要性 0.0-1.0)
  - embedding: vector (向量嵌入)
  - created_at: str (创建时间)
  - metadata: dict (额外元数据)

存储格式：
  paper_id = "memory_{user_id}"
  title = "User Memory: {memory_type}"
```

---

## 配置参数总览

### 环境变量

```bash
# 短期记忆
SLIDING_WINDOW_SIZE=10              # 滑动窗口大小
MAX_CONTEXT_TOKENS=4000              # 最大上下文Token
ENABLE_TOKEN_COUNTING=true           # 启用Token计数
ENABLE_CHECKPOINTER=true             # 启用Checkpointer
CHECKPOINT_TTL=86400                 # Checkpoint TTL（秒）

# 中期记忆
ENABLE_CONVERSATION_SUMMARY=true     # 启用对话摘要
SUMMARY_THRESHOLD=20                 # 摘要触发阈值
SUMMARY_MAX_TOKENS=500               # 摘要最大Token

# 长期记忆
ENABLE_SEMANTIC_MEMORY=true          # 启用语义记忆
SEMANTIC_MEMORY_TOP_K=5              # 检索记忆数量
MEMORY_IMPORTANCE_THRESHOLD=0.7      # 重要性阈值

# 基础设施
REDIS_URL=redis://localhost:6379/0  # Redis 地址
VECTOR_SEARCH_SERVICE_URL=http://... # 向量服务地址
CONVERSATION_SERVICE_URL=http://...  # 对话服务地址
```

---

## 性能优化

### 1. 缓存策略
- **对话历史**：Redis 缓存，6 小时 TTL
- **对话摘要**：Redis 缓存，支持增量更新
- **Checkpoint**：Redis 存储，24 小时 TTL

### 2. 异步处理
- **对话摘要生成**：异步执行，不阻塞响应
- **语义记忆存储**：对话结束后异步提取
- **对话历史持久化**：后台队列异步写入

### 3. 智能压缩
- **双重压缩**：摘要 + 滑动窗口
- **Token 感知**：精确控制上下文长度
- **优先级保留**：system 消息、工具结果优先

---

## 优势与特点

### ✅ 优势

1. **分层设计**：短期、中期、长期记忆分离，职责清晰
2. **性能优化**：缓存 + 异步，响应速度快
3. **成本控制**：Token 精确控制，降低 API 成本
4. **个性化**：语义记忆支持跨会话个性化
5. **可扩展**：各层可独立启用/禁用

### ⚠️ 注意事项

1. **Redis 依赖**：短期和中期记忆依赖 Redis，需要高可用
2. **向量服务**：长期记忆依赖 Milvus，需要稳定服务
3. **LLM 成本**：摘要和记忆提取需要调用 LLM，有额外成本
4. **配置调优**：需要根据实际场景调整阈值和参数

---

## 长时间对话恢复

### 问题场景

用户可能在**几天、几周甚至几个月后**想继续之前的对话。此时：
- Redis 缓存已过期（6小时TTL）
- Checkpointer 已过期（24小时TTL）
- 对话摘要缓存可能已过期
- 但 conversation-service 中保存着完整的对话历史

### 现有机制

✅ **已支持**：
1. **持久化存储**：所有对话消息保存在 `conversation-service` 数据库
2. **自动恢复**：缓存未命中时自动从数据库加载完整历史
3. **智能处理**：加载后自动应用摘要和滑动窗口

⚠️ **潜在问题**：
1. 超长对话（几百条）加载可能较慢
2. 摘要缓存过期后需要重新生成（调用LLM）
3. 没有明确的恢复提示

### 优化建议

详见：[对话恢复策略文档](./CONVERSATION_RESUME_STRATEGY.md)

**核心优化**：
1. **智能加载**：根据对话长度选择加载策略
2. **摘要持久化**：将摘要保存到数据库，避免重复生成
3. **恢复提示**：明确告知用户对话已恢复
4. **分页加载**：优化超长对话的加载性能

---

## 未来改进方向

1. **记忆衰减**：自动清理过时记忆
2. **记忆合并**：合并相似记忆，避免冗余
3. **记忆重要性动态调整**：根据使用频率调整重要性
4. **多模态记忆**：支持图片、文档等记忆类型
5. **记忆可视化**：提供用户记忆管理界面
6. **智能对话恢复**：优化长时间未使用对话的恢复体验

---

## 总结

ResearchGO Agent 的三层记忆架构是一个**设计精良、层次清晰**的记忆系统：

- **短期记忆**：通过滑动窗口和 Checkpointer 管理单次对话上下文
- **中期记忆**：通过摘要和缓存优化长对话性能
- **长期记忆**：通过语义记忆实现跨会话个性化

三层记忆系统协同工作，在保持上下文连贯性的同时，有效控制了 Token 消耗和存储成本，为用户提供了流畅的对话体验。
