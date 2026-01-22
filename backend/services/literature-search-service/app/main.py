"""
Literature Search Service - Main Application
基于 OpenAlex 的学术文献检索服务
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

# 创建FastAPI应用
app = FastAPI(
    title="Literature Search Service",
    description="基于 OpenAlex 的学术文献检索微服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.api import literature
app.include_router(literature.router)

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 50)
    logger.info("📚 Literature Search Service 启动中...")
    logger.info("=" * 50)
    logger.info(f"📖 OpenAlex API: https://api.openalex.org")
    logger.info(f"📧 Contact Email: {os.getenv('CONTACT_EMAIL', 'Not configured')}")
    logger.info(f"🤖 OpenAI Model: {os.getenv('OPENAI_MODEL', 'gpt-4o')}")
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("📚 Literature Search Service 已关闭")

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Literature Search Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

