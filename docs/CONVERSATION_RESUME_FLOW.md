# 对话恢复流程验证

## ✅ 现有实现已支持

**是的，Agent 已经能够获取最近的对话和摘要缓存并注入上下文！**

## 完整工作流程

### 1. 用户继续之前的对话

```
用户发送消息 + conversation_id
    ↓
API: agent_chat() 接收请求
```

### 2. 加载对话历史

```python
# app/api/agent.py:84
conversation_history = await cache.load_history(conversation_id, token)
```

**流程**：
1. **先查 Redis 缓存** (`conv_history:{conversation_id}`)
   - 如果缓存命中（6小时内）：直接返回 ✅
   - 如果缓存未命中：继续下一步

2. **从 conversation-service 加载**
   - 调用 `GET /api/conversations/{id}/messages`
   - 获取完整对话历史
   - 写入 Redis 缓存（6小时TTL）

3. **返回对话历史**

### 3. 处理摘要和窗口消息

```python
# app/agent/graph.py:169
summary_result = await summary_manager.process(
    messages=messages,
    conversation_id=conversation_id,
    window_size=SLIDING_WINDOW_SIZE
)
```

**流程**：
1. **检查摘要缓存** (`summary:{conversation_id}`)
   ```python
   # app/memory/summary.py:209
   cached = await self._get_cached_summary(conversation_id)
   ```
   - 如果缓存存在且有效：直接使用 ✅
   - 如果缓存不存在或过期：继续下一步

2. **生成/更新摘要**
   - 首次生成：调用 LLM 生成摘要
   - 增量更新：合并旧摘要和新消息
   - 缓存摘要（**无TTL，永久保存**）

3. **返回摘要 + 窗口消息**
   ```python
   SummaryResult(
       summary=cached_summary,  # 缓存的摘要
       window_messages=window_messages,  # 最近的消息
       from_cache=True  # 标记来自缓存
   )
   ```

### 4. 应用滑动窗口

```python
# app/agent/graph.py:186
processed_messages, window_stats = self.sliding_window.apply(
    processed_messages,  # 已经是窗口消息了
    strategy="hybrid"
)
```

进一步压缩，确保不超过 Token 限制。

### 5. 检索语义记忆

```python
# app/agent/graph.py:198
memory_context = await semantic_memory.get_user_context(
    user_id=user_id,
    current_query=user_input,
    token=token
)
```

从向量数据库检索相关的用户记忆。

### 6. 注入上下文到 System Prompt

```python
# app/agent/graph.py:233-241
memory_section = ""
if summary or memory_context:
    memory_section = "\n\n--- 上下文信息 ---"
    if summary:
        memory_section += f"\n[对话摘要]: {summary}"  # ✅ 注入摘要
    if memory_context:
        memory_section += f"\n[用户背景]:\n{memory_context}"  # ✅ 注入记忆
    memory_section += "\n--- 上下文结束 ---\n"

# 注入到 System Prompt
SystemMessage(content=SYSTEM_PROMPT.format(
    tool_descriptions=...,
    memory_context=memory_section,  # ✅ 注入上下文
    degraded_tools_notice=...
))
```

### 7. 构建最终消息列表

```python
messages = [
    SystemMessage(content=...),  # 包含摘要和记忆上下文
    # ... 处理后的历史消息（窗口消息）
    HumanMessage(content=user_input)  # 当前用户输入
]
```

### 8. LLM 推理

LLM 接收到：
- ✅ **对话摘要**：之前对话的关键信息
- ✅ **最近消息**：最近的对话内容
- ✅ **用户记忆**：相关的用户偏好和背景
- ✅ **当前输入**：用户的新消息

---

## 缓存机制详解

### 对话历史缓存

```python
# Redis Key: conv_history:{conversation_id}
# TTL: 6小时
# 存储: JSON 格式的消息列表
```

**特点**：
- ✅ 快速读取（毫秒级）
- ⚠️ 6小时后过期，需要从数据库重新加载
- ✅ 加载后自动重新缓存

### 摘要缓存

```python
# Redis Keys:
#   summary:{conversation_id} -> 摘要内容
#   summary_meta:{conversation_id} -> 元数据（消息数、更新时间）
# TTL: 无（永久保存，直到Redis重启）
```

**特点**：
- ✅ 永久保存（不会过期）
- ✅ 支持增量更新
- ⚠️ Redis 重启后会丢失，需要重新生成

### Checkpointer 缓存

```python
# Redis Keys:
#   checkpoint:{thread_id}:{checkpoint_id} -> Agent状态
#   checkpoint_latest:{thread_id} -> 最新checkpoint
# TTL: 24小时
```

**特点**：
- ✅ 保存完整的 Agent 状态
- ⚠️ 24小时后过期
- ℹ️ 主要用于多轮对话中的状态恢复

---

## 实际场景验证

### 场景1：6小时内继续对话

```
用户继续对话（<6小时）
    ↓
✅ 对话历史：Redis 缓存命中
✅ 摘要：Redis 缓存命中
✅ 结果：毫秒级加载，完美恢复上下文
```

### 场景2：6小时-24小时继续对话

```
用户继续对话（6-24小时）
    ↓
⚠️ 对话历史：缓存过期，从数据库加载（稍慢）
✅ 摘要：Redis 缓存命中（永久保存）
✅ 结果：加载稍慢，但摘要和上下文完整
```

### 场景3：几天后继续对话

```
用户继续对话（几天后）
    ↓
⚠️ 对话历史：缓存过期，从数据库加载
✅ 摘要：Redis 缓存命中（如果Redis未重启）
✅ 结果：需要加载完整历史，但摘要可用
```

### 场景4：Redis 重启后继续对话

```
Redis 重启后继续对话
    ↓
⚠️ 对话历史：缓存丢失，从数据库加载
⚠️ 摘要：缓存丢失，需要重新生成（调用LLM）
✅ 结果：可以恢复，但需要重新生成摘要（增加成本）
```

---

## 优化建议

### 1. 摘要持久化（推荐）

**问题**：摘要只存在 Redis，重启后会丢失

**方案**：将摘要持久化到数据库
```python
# 在 conversation-service 添加字段
class Conversation:
    summary: Optional[str] = None
    summary_updated_at: Optional[datetime] = None
```

**优势**：
- ✅ 摘要永久保存
- ✅ Redis 重启不影响
- ✅ 恢复对话时无需重新生成

### 2. 摘要缓存 TTL

**问题**：摘要缓存无TTL，可能占用内存

**方案**：设置合理的TTL（如30天）
```python
# app/memory/summary.py:119
pipe.setex(self._summary_key(conversation_id), 30*24*3600, summary)
```

### 3. 智能加载策略

**问题**：超长对话加载所有历史可能很慢

**方案**：根据对话长度选择策略
- 短对话（<50条）：完整加载
- 长对话（>50条）：只加载最近50条 + 摘要

---

## 总结

### ✅ 已实现的功能

1. **对话历史恢复**：从缓存或数据库加载
2. **摘要缓存使用**：优先使用缓存的摘要
3. **上下文注入**：摘要和记忆都注入到 System Prompt
4. **窗口消息**：只保留最近的消息，节省 Token

### ⚠️ 潜在问题

1. **摘要丢失**：Redis 重启后摘要会丢失
2. **加载性能**：超长对话加载可能较慢
3. **成本控制**：摘要丢失后需要重新生成（调用LLM）

### 🚀 建议优化

1. **摘要持久化**：保存到数据库（P0）
2. **智能加载**：根据对话长度选择策略（P1）
3. **缓存TTL**：为摘要设置合理的过期时间（P2）

---

## 验证代码

可以通过以下方式验证：

```python
# 1. 检查对话历史缓存
redis_client.get("conv_history:123")

# 2. 检查摘要缓存
redis_client.get("summary:123")
redis_client.get("summary_meta:123")

# 3. 查看日志
# 应该看到：
# - "Cache HIT for conversation 123" 或
# - "Cache MISS for conversation 123, loading from service"
# - "Using cached summary for conversation 123" 或
# - "Generated new summary for conversation 123"
```
