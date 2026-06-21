# 长时间对话恢复策略

## 问题场景

用户可能在**几天、几周甚至几个月后**想继续之前的对话。此时：
- Redis 缓存已过期（6小时TTL）
- Checkpointer 已过期（24小时TTL）
- 对话摘要缓存可能已过期
- 但 conversation-service 中保存着完整的对话历史

## 现有机制分析

### ✅ 已支持的功能

1. **对话历史持久化**
   - 所有对话消息都保存在 `conversation-service` 的数据库中
   - 即使缓存过期，也能从数据库恢复

2. **自动加载机制**
   ```python
   # app/memory/conversation_cache.py
   async def load_history(conversation_id, token):
       # 1. 先查 Redis 缓存
       cached = await client.get(cache_key)
       if cached:
           return json.loads(cached)  # 缓存命中
       
       # 2. 缓存未命中，从 conversation-service 加载
       response = await http_client.get(
           f"{service_url}/api/conversations/{conversation_id}/messages"
       )
       # 3. 加载后写入缓存
       await client.setex(cache_key, ttl, json.dumps(history))
   ```

3. **智能上下文处理**
   - 自动应用对话摘要（如果对话很长）
   - 应用滑动窗口进一步压缩
   - 检索相关语义记忆

### ⚠️ 潜在问题

1. **性能问题**
   - 如果对话非常长（几百条消息），加载所有历史可能很慢
   - 摘要缓存过期后需要重新生成（调用LLM，可能慢）

2. **用户体验**
   - 没有明确的"恢复对话"提示
   - 用户不知道系统是否成功恢复了上下文

3. **资源消耗**
   - 加载完整历史可能占用大量内存
   - 重新生成摘要需要调用LLM，增加成本

---

## 优化方案

### 方案1：智能加载策略（推荐）

**核心思想**：根据对话长度和最后使用时间，选择不同的加载策略

```python
async def load_history_smart(
    self,
    conversation_id: Union[str, int],
    token: str,
    force_full: bool = False
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    智能加载对话历史
    
    策略：
    1. 短对话（<50条）或最近使用（<7天）：加载完整历史
    2. 长对话且很久未用（>7天）：只加载最近消息 + 摘要
    3. 超长对话（>200条）：分页加载
    """
    # 1. 获取对话元数据（最后使用时间、消息数）
    metadata = await self._get_conversation_metadata(conversation_id, token)
    message_count = metadata.get("message_count", 0)
    last_used = metadata.get("last_used_at")
    days_since_last_use = self._days_since(last_used) if last_used else 999
    
    # 2. 检查缓存
    cached = await self._get_cached_history(conversation_id)
    if cached and days_since_last_use < 1:
        return cached, {"source": "cache", "strategy": "cached"}
    
    # 3. 选择加载策略
    if force_full or message_count < 50 or days_since_last_use < 7:
        # 策略A：加载完整历史
        history = await self._load_full_history(conversation_id, token)
        return history, {"source": "database", "strategy": "full"}
    
    elif message_count > 200:
        # 策略B：分页加载（只加载最近N条）
        history = await self._load_recent_history(
            conversation_id, token, limit=100
        )
        summary = await self._get_or_generate_summary(
            conversation_id, token, use_cache=True
        )
        return history, {
            "source": "database",
            "strategy": "recent_with_summary",
            "summary": summary,
            "total_messages": message_count
        }
    
    else:
        # 策略C：加载最近消息 + 摘要
        history = await self._load_recent_history(
            conversation_id, token, limit=50
        )
        summary = await self._get_or_generate_summary(
            conversation_id, token, use_cache=True
        )
        return history, {
            "source": "database",
            "strategy": "recent_with_summary",
            "summary": summary,
            "total_messages": message_count
        }
```

**优势**：
- 根据实际情况选择最优策略
- 减少不必要的加载和计算
- 提升用户体验

---

### 方案2：摘要持久化

**核心思想**：将生成的摘要持久化到数据库，而不是只存在Redis

```python
# 在 conversation-service 中添加摘要字段
class Conversation(Base):
    id: int
    title: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None  # 新增：持久化摘要
    summary_updated_at: Optional[datetime] = None
    message_count: int = 0
```

**工作流程**：
1. 生成摘要后，同步保存到数据库
2. 恢复对话时，优先从数据库加载摘要
3. 如果摘要过期（比如30天），重新生成

**优势**：
- 摘要不会因为Redis过期而丢失
- 恢复对话时无需重新生成摘要
- 可以显示"上次对话摘要"给用户

---

### 方案3：对话恢复提示

**核心思想**：在恢复长时间未使用的对话时，给用户明确的提示

```python
async def _prepare_context_with_resume_info(...):
    """准备上下文，包含恢复信息"""
    processed_messages, summary, memory_context = await self._prepare_context(...)
    
    # 检查是否是恢复的对话
    resume_info = await self._check_resume_status(conversation_id)
    
    if resume_info.get("is_resumed"):
        # 在上下文中添加恢复提示
        resume_notice = f"""
[系统提示] 您正在继续 {resume_info['days_ago']} 天前的对话。
对话共 {resume_info['total_messages']} 条消息，已为您加载最近 {len(processed_messages)} 条。
之前的对话摘要：{summary}
"""
        # 可以注入到 system prompt 或作为第一条消息
        ...
    
    return processed_messages, summary, memory_context, resume_info
```

**前端展示**：
```javascript
// 如果检测到是恢复的对话
if (resumeInfo.isResumed) {
  showNotification({
    type: 'info',
    message: `正在恢复 ${resumeInfo.daysAgo} 天前的对话...`,
    duration: 3000
  });
}
```

---

### 方案4：分页加载优化

**核心思想**：对于超长对话，使用分页加载，只加载必要的历史

```python
async def _load_recent_history(
    self,
    conversation_id: Union[str, int],
    token: str,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    分页加载最近的消息
    
    只加载最近的N条消息，而不是全部历史
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.service_url}/api/conversations/{conversation_id}/messages",
                params={
                    "limit": limit,
                    "offset": offset,
                    "order": "desc"  # 从最新开始
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                messages = response.json()
                # 反转顺序（从旧到新）
                return list(reversed(messages))
    except Exception as e:
        logger.error(f"Error loading recent history: {e}")
        return []
```

**优势**：
- 减少网络传输
- 降低内存占用
- 提升加载速度

---

## 推荐实现方案

### 阶段1：基础优化（立即实施）

1. **添加对话元数据查询**
   ```python
   async def _get_conversation_metadata(
       self, conversation_id: str, token: str
   ) -> Dict[str, Any]:
       """获取对话元数据（消息数、最后使用时间等）"""
       # 从 conversation-service 获取
   ```

2. **智能加载策略**
   - 短对话（<50条）：完整加载
   - 长对话（>50条）：最近50条 + 摘要

3. **恢复提示**
   - 检测对话是否很久未用（>7天）
   - 在响应中添加恢复提示

### 阶段2：持久化优化（中期）

1. **摘要持久化**
   - 在 conversation-service 添加摘要字段
   - 摘要生成后持久化
   - 恢复时优先使用持久化摘要

2. **分页加载**
   - 支持分页加载消息
   - 优化超长对话的加载性能

### 阶段3：高级优化（长期）

1. **智能摘要更新**
   - 检测摘要是否过期
   - 增量更新摘要，而不是重新生成

2. **对话压缩**
   - 自动压缩旧消息
   - 保留关键信息，删除冗余

---

## 实现示例

### 1. 增强 ConversationCache

```python
class ConversationCache:
    async def load_history_smart(
        self,
        conversation_id: Union[str, int],
        token: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """智能加载对话历史"""
        # 1. 获取元数据
        metadata = await self._get_conversation_metadata(conversation_id, token)
        message_count = metadata.get("message_count", 0")
        last_used = metadata.get("last_used_at")
        
        # 2. 检查缓存
        cached = await self._get_cached_history(conversation_id)
        if cached:
            return cached, {"source": "cache"}
        
        # 3. 选择策略
        if message_count < 50:
            # 短对话：完整加载
            history = await self._load_full_history(conversation_id, token)
            await self._cache_history(conversation_id, history)
            return history, {"source": "database", "strategy": "full"}
        else:
            # 长对话：最近消息 + 摘要
            history = await self._load_recent_history(
                conversation_id, token, limit=50
            )
            summary = await self._get_persisted_summary(conversation_id, token)
            
            return history, {
                "source": "database",
                "strategy": "recent_with_summary",
                "summary": summary,
                "total_messages": message_count,
                "is_resumed": self._is_old_conversation(last_used)
            }
    
    def _is_old_conversation(self, last_used: Optional[datetime]) -> bool:
        """判断是否是旧对话"""
        if not last_used:
            return False
        days_ago = (datetime.now() - last_used).days
        return days_ago > 7
```

### 2. 增强 Agent 上下文准备

```python
async def _prepare_context(
    self,
    messages: List[Dict[str, Any]],
    user_id: Optional[str],
    user_input: str,
    conversation_id: Optional[str],
    token: Optional[str]
) -> tuple[List[Dict[str, Any]], str, str, Dict[str, Any]]:
    """准备上下文，返回恢复信息"""
    summary = ""
    memory_context = ""
    resume_info = {}
    processed_messages = messages
    
    # 检查是否是恢复的对话
    if conversation_id:
        cache = get_conversation_cache()
        history, load_info = await cache.load_history_smart(conversation_id, token)
        
        if load_info.get("is_resumed"):
            resume_info = {
                "is_resumed": True,
                "total_messages": load_info.get("total_messages", 0),
                "strategy": load_info.get("strategy", "full")
            }
        
        # 如果有摘要，使用它
        if load_info.get("summary"):
            summary = load_info["summary"]
            processed_messages = history
    
    # ... 其余处理逻辑 ...
    
    return processed_messages, summary, memory_context, resume_info
```

### 3. 在 System Prompt 中注入恢复信息

```python
if resume_info.get("is_resumed"):
    resume_notice = f"""
[对话恢复提示]
您正在继续之前的对话。对话共 {resume_info['total_messages']} 条消息。
为了保持上下文连贯，已为您加载最近的消息和之前的对话摘要。
"""
    memory_section += f"\n{resume_notice}"
```

---

## 配置参数

```python
# 对话恢复配置
CONVERSATION_RESUME_THRESHOLD_DAYS = 7      # 多少天未使用算"旧对话"
CONVERSATION_FULL_LOAD_THRESHOLD = 50      # 多少条消息以下完整加载
CONVERSATION_RECENT_MESSAGES_LIMIT = 50    # 恢复时加载最近N条消息
CONVERSATION_SUMMARY_TTL_DAYS = 30         # 摘要有效期（天）
```

---

## 总结

### ✅ 现有机制已支持
- 从 conversation-service 恢复完整历史
- 自动应用摘要和滑动窗口
- 缓存优化加载性能

### 🚀 建议优化
1. **智能加载策略**：根据对话长度和最后使用时间选择策略
2. **摘要持久化**：避免重复生成摘要
3. **恢复提示**：明确告知用户对话已恢复
4. **分页加载**：优化超长对话的加载性能

### 📊 预期效果
- **加载速度**：提升 50-80%（长对话场景）
- **用户体验**：明确的恢复提示，更好的上下文连贯性
- **成本控制**：减少不必要的LLM调用（摘要生成）

---

## 实施优先级

1. **P0（立即）**：智能加载策略 + 恢复提示
2. **P1（1周内）**：摘要持久化
3. **P2（1月内）**：分页加载优化
4. **P3（长期）**：智能摘要更新
