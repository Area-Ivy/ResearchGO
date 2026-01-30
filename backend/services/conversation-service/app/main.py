"""
对话服务主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

from app.api import conversations_router
from app.database import init_db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Conversation Service",
    description="对话服务 - 管理对话历史和消息",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# 包含路由
app.include_router(conversations_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "conversation-service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("=" * 60)
    logger.info("启动对话服务 (Conversation Service)...")
    logger.info("💬 提供功能: 对话管理、消息管理")
    
    # Register to Consul
    try:
        from app.utils.consul_registry import register_service
        await register_service()
    except Exception as e:
        logger.warning(f"Consul registration failed: {e}")
    
    try:
        init_db()
        logger.info("✓ 数据库初始化成功")
    except Exception as e:
        logger.error(f"⚠️  数据库初始化失败: {e}")
    
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    # Deregister from Consul
    try:
        from app.utils.consul_registry import deregister_service
        await deregister_service()
    except Exception as e:
        logger.warning(f"Consul deregistration failed: {e}")
    
    logger.info("关闭对话服务...")

