"""
Chat Service - Main Application
AI 聊天微服务
"""
import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Chat Service",
    description="AI 聊天微服务 - 基于 OpenAI 的智能对话",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.api import chat_router
app.include_router(chat_router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 50)
    logger.info("💬 Chat Service 启动中...")
    logger.info("=" * 50)
    
    # 检查 OpenAI 配置
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        logger.info(f"✓ OPENAI_API_KEY: 已配置 ({api_key[:8]}...)")
    else:
        logger.warning("⚠️ OPENAI_API_KEY: 未配置!")
    
    base_url = os.getenv('OPENAI_BASE_URL')
    if base_url:
        logger.info(f"✓ OPENAI_BASE_URL: {base_url}")
    
    model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    logger.info(f"✓ 默认模型: {model}")
    
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("💬 Chat Service 已关闭")


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Chat Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

