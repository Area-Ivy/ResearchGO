"""
Agent Service Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Microservices URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
CONVERSATION_SERVICE_URL = os.getenv("CONVERSATION_SERVICE_URL", "http://localhost:8002")
PAPER_STORAGE_SERVICE_URL = os.getenv("PAPER_STORAGE_SERVICE_URL", "http://localhost:8003")
VECTOR_SEARCH_SERVICE_URL = os.getenv("VECTOR_SEARCH_SERVICE_URL", "http://localhost:8004")
LITERATURE_SERVICE_URL = os.getenv("LITERATURE_SERVICE_URL", "http://localhost:8005")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://localhost:8006")
MINDMAP_SERVICE_URL = os.getenv("MINDMAP_SERVICE_URL", "http://localhost:8007")
ANALYSIS_SERVICE_URL = os.getenv("ANALYSIS_SERVICE_URL", "http://localhost:8008")

# Agent Configuration
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))
AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "120"))  # seconds

# ============ Memory System Configuration ============

# 1. 短期记忆 - 滑动窗口配置
SLIDING_WINDOW_SIZE = int(os.getenv("SLIDING_WINDOW_SIZE", "10"))  # 保留最近N轮对话
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "4000"))  # 最大上下文token数
ENABLE_TOKEN_COUNTING = os.getenv("ENABLE_TOKEN_COUNTING", "true").lower() == "true"

# 2. 长对话摘要配置
ENABLE_CONVERSATION_SUMMARY = os.getenv("ENABLE_CONVERSATION_SUMMARY", "true").lower() == "true"
SUMMARY_THRESHOLD = int(os.getenv("SUMMARY_THRESHOLD", "20"))  # 超过N条消息时生成摘要
SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "500"))  # 摘要最大token数

# 3. 语义记忆配置
ENABLE_SEMANTIC_MEMORY = os.getenv("ENABLE_SEMANTIC_MEMORY", "true").lower() == "true"
SEMANTIC_MEMORY_TOP_K = int(os.getenv("SEMANTIC_MEMORY_TOP_K", "5"))  # 检索相关记忆数量
MEMORY_IMPORTANCE_THRESHOLD = float(os.getenv("MEMORY_IMPORTANCE_THRESHOLD", "0.7"))  # 重要性阈值

# 4. Redis Checkpointer 配置
ENABLE_CHECKPOINTER = os.getenv("ENABLE_CHECKPOINTER", "true").lower() == "true"
CHECKPOINT_TTL = int(os.getenv("CHECKPOINT_TTL", "86400"))  # checkpoint 过期时间(秒)，默认24小时

