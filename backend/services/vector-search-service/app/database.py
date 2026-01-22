"""
Milvus连接配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Milvus配置
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "research_papers")

