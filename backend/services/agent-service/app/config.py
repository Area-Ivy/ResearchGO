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

