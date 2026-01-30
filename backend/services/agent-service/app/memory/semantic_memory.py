"""
Semantic Memory Service

语义记忆服务：基于向量数据库的跨会话长期记忆
- 存储用户的重要信息和偏好
- 支持语义检索相关记忆
- 自动评估记忆重要性
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import httpx
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import (
    VECTOR_SEARCH_SERVICE_URL,
    ENABLE_SEMANTIC_MEMORY,
    SEMANTIC_MEMORY_TOP_K,
    MEMORY_IMPORTANCE_THRESHOLD,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_BASE_URL
)

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """记忆类型"""
    USER_PREFERENCE = "user_preference"      # 用户偏好
    RESEARCH_INTEREST = "research_interest"  # 研究兴趣
    KEY_FINDING = "key_finding"              # 重要发现
    TASK_CONTEXT = "task_context"            # 任务上下文
    FEEDBACK = "feedback"                    # 用户反馈


@dataclass
class Memory:
    """记忆条目"""
    id: str
    user_id: str
    content: str
    memory_type: MemoryType
    importance: float  # 0.0 - 1.0
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 0.0  # 检索时的相关性分数


@dataclass
class MemoryExtractionResult:
    """记忆提取结果"""
    memories: List[Dict[str, Any]]
    has_important_info: bool


class SemanticMemoryService:
    """
    语义记忆服务
    
    功能：
    1. 从对话中提取重要信息
    2. 存储到向量数据库（复用现有的 Milvus）
    3. 语义检索相关记忆
    4. 自动衰减和清理旧记忆
    
    存储设计：
    - 使用单独的 Milvus Collection: user_memories
    - 字段: user_id, content, memory_type, importance, embedding, created_at
    """
    
    COLLECTION_NAME = "user_memories"
    
    def __init__(
        self,
        vector_service_url: str = VECTOR_SEARCH_SERVICE_URL,
        top_k: int = SEMANTIC_MEMORY_TOP_K,
        importance_threshold: float = MEMORY_IMPORTANCE_THRESHOLD
    ):
        self.vector_service_url = vector_service_url
        self.top_k = top_k
        self.importance_threshold = importance_threshold
        
        # 初始化 LLM（用于提取记忆）
        llm_kwargs = {
            "model": OPENAI_MODEL,
            "temperature": 0.3,
            "api_key": OPENAI_API_KEY,
        }
        if OPENAI_BASE_URL:
            llm_kwargs["base_url"] = OPENAI_BASE_URL
        
        self.llm = ChatOpenAI(**llm_kwargs)
    
    async def _call_vector_service(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用向量搜索服务"""
        url = f"{self.vector_service_url}{endpoint}"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=data, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
    
    async def extract_memories(
        self,
        messages: List[Dict[str, Any]],
        user_id: str
    ) -> MemoryExtractionResult:
        """
        从对话中提取值得记住的信息
        
        提取类型：
        1. 用户偏好（如：喜欢简洁的回答）
        2. 研究兴趣（如：关注 transformer 领域）
        3. 重要发现（如：找到了有价值的论文）
        4. 任务上下文（如：正在写关于 X 的论文）
        """
        if not ENABLE_SEMANTIC_MEMORY:
            return MemoryExtractionResult(memories=[], has_important_info=False)
        
        # 只分析最近的对话
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        
        # 构建对话文本
        conversation_text = []
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:300]
            if role in ["user", "assistant"]:
                conversation_text.append(f"{role}: {content}")
        
        if not conversation_text:
            return MemoryExtractionResult(memories=[], has_important_info=False)
        
        conversation_str = "\n".join(conversation_text)
        
        prompt = f"""分析以下对话，提取值得长期记住的用户信息。

对话内容：
{conversation_str}

请以 JSON 格式输出，提取以下类型的信息（如果有的话）：
1. user_preference: 用户的偏好和习惯
2. research_interest: 用户的研究兴趣和关注领域
3. key_finding: 对话中发现的重要信息
4. task_context: 用户当前的任务或项目背景

输出格式：
{{
  "memories": [
    {{
      "type": "research_interest",
      "content": "用户正在研究大语言模型在医学领域的应用",
      "importance": 0.8
    }}
  ],
  "has_important_info": true
}}

如果没有值得记住的信息，返回 {{"memories": [], "has_important_info": false}}

请只返回 JSON，不要其他内容："""
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="你是一个信息提取专家，善于从对话中识别重要信息。只返回有效的 JSON。"),
                HumanMessage(content=prompt)
            ])
            
            # 解析 JSON
            result_text = response.content.strip()
            # 处理可能的 markdown 代码块
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            
            # 过滤低重要性记忆
            filtered_memories = [
                m for m in result.get("memories", [])
                if m.get("importance", 0) >= self.importance_threshold
            ]
            
            return MemoryExtractionResult(
                memories=filtered_memories,
                has_important_info=result.get("has_important_info", False)
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse memory extraction result: {e}")
            return MemoryExtractionResult(memories=[], has_important_info=False)
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
            return MemoryExtractionResult(memories=[], has_important_info=False)
    
    async def store_memory(
        self,
        user_id: str,
        content: str,
        memory_type: MemoryType,
        importance: float,
        token: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        存储记忆到向量数据库
        
        注意：这里复用 vector-search-service 的能力
        实际存储时，使用特殊的 paper_id 格式：memory_{user_id}
        """
        if not ENABLE_SEMANTIC_MEMORY:
            return False
        
        try:
            memory_doc = {
                "paper_id": f"memory_{user_id}",
                "title": f"User Memory: {memory_type.value}",
                "file_name": f"memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "content": content,
                "max_chunk_size": 1000,  # 记忆通常较短
                "structured_chunks": [{
                    "content": content,
                    "section_type": memory_type.value,
                    "section_title": memory_type.value,
                    "hierarchy_path": f"Memory > {memory_type.value}",
                    "char_count": len(content),
                    "is_complete_section": True,
                    "metadata": {
                        "user_id": user_id,
                        "importance": importance,
                        "memory_type": memory_type.value,
                        **(metadata or {})
                    }
                }]
            }
            
            result = await self._call_vector_service(
                "POST",
                "/api/vector/index",
                data=memory_doc,
                token=token
            )
            
            logger.info(f"Stored memory for user {user_id}: {memory_type.value}")
            return result.get("success", True)
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False
    
    async def recall_relevant(
        self,
        user_id: str,
        query: str,
        token: str,
        top_k: Optional[int] = None
    ) -> List[Memory]:
        """
        检索与查询相关的记忆
        """
        if not ENABLE_SEMANTIC_MEMORY:
            return []
        
        top_k = top_k or self.top_k
        
        try:
            # 使用混合检索搜索用户记忆
            result = await self._call_vector_service(
                "POST",
                "/api/vector/hybrid-search",
                data={
                    "query": query,
                    "top_k": top_k,
                    "paper_id": f"memory_{user_id}",  # 限定在用户记忆中搜索
                    "use_reranker": True,
                    "translate_query": False  # 记忆通常是中文
                },
                token=token
            )
            
            memories = []
            for hit in result.get("results", []):
                # 从 metadata 中提取记忆信息
                source = hit.get("source", "")
                
                memories.append(Memory(
                    id=hit.get("chunk_id", ""),
                    user_id=user_id,
                    content=hit.get("content", ""),
                    memory_type=MemoryType(source) if source in [t.value for t in MemoryType] else MemoryType.TASK_CONTEXT,
                    importance=0.8,  # 检索到的记忆默认重要
                    created_at=hit.get("upload_time", ""),
                    relevance_score=hit.get("relevance_score", 0)
                ))
            
            logger.info(f"Recalled {len(memories)} memories for user {user_id}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return []
    
    async def get_user_context(
        self,
        user_id: str,
        current_query: str,
        token: str
    ) -> str:
        """
        获取用户上下文：将相关记忆格式化为上下文字符串
        """
        if not ENABLE_SEMANTIC_MEMORY:
            return ""
        
        memories = await self.recall_relevant(user_id, current_query, token)
        
        if not memories:
            return ""
        
        # 按类型分组
        by_type: Dict[str, List[str]] = {}
        for m in memories:
            type_name = m.memory_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(m.content)
        
        # 格式化输出
        context_parts = []
        
        if "research_interest" in by_type:
            context_parts.append(f"用户研究兴趣: {'; '.join(by_type['research_interest'][:3])}")
        
        if "user_preference" in by_type:
            context_parts.append(f"用户偏好: {'; '.join(by_type['user_preference'][:2])}")
        
        if "task_context" in by_type:
            context_parts.append(f"当前任务: {'; '.join(by_type['task_context'][:2])}")
        
        if "key_finding" in by_type:
            context_parts.append(f"之前发现: {'; '.join(by_type['key_finding'][:2])}")
        
        return "\n".join(context_parts)
    
    async def process_and_store(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        token: str
    ) -> int:
        """
        处理对话并存储提取的记忆
        
        Returns:
            存储的记忆数量
        """
        if not ENABLE_SEMANTIC_MEMORY:
            return 0
        
        # 提取记忆
        extraction_result = await self.extract_memories(messages, user_id)
        
        if not extraction_result.has_important_info:
            return 0
        
        # 存储每条记忆
        stored_count = 0
        for memory in extraction_result.memories:
            try:
                memory_type = MemoryType(memory.get("type", "task_context"))
            except ValueError:
                memory_type = MemoryType.TASK_CONTEXT
            
            success = await self.store_memory(
                user_id=user_id,
                content=memory.get("content", ""),
                memory_type=memory_type,
                importance=memory.get("importance", 0.7),
                token=token
            )
            
            if success:
                stored_count += 1
        
        logger.info(f"Stored {stored_count} memories for user {user_id}")
        return stored_count
    
    async def clear_user_memories(self, user_id: str, token: str) -> bool:
        """清除用户的所有记忆"""
        try:
            await self._call_vector_service(
                "DELETE",
                f"/api/vector/delete/memory_{user_id}",
                token=token
            )
            logger.info(f"Cleared all memories for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            return False


# 全局实例
_semantic_memory_service: Optional[SemanticMemoryService] = None


def get_semantic_memory_service() -> SemanticMemoryService:
    """获取语义记忆服务单例"""
    global _semantic_memory_service
    if _semantic_memory_service is None:
        _semantic_memory_service = SemanticMemoryService()
        logger.info("Initialized SemanticMemoryService")
    return _semantic_memory_service

