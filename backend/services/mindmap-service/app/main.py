"""
Mindmap Service - Main Application
思维导图生成微服务
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
    title="Mindmap Service",
    description="思维导图生成微服务 - 基于 AI 分析 PDF 生成思维导图",
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
from app.api import mindmap_router
app.include_router(mindmap_router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 50)
    logger.info("🧠 Mindmap Service 启动中...")
    logger.info("=" * 50)
    
    # 检查配置
    minio_endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    logger.info(f"📦 MinIO: {minio_endpoint}")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        logger.info(f"✓ OPENAI_API_KEY: 已配置 ({api_key[:8]}...)")
    else:
        logger.warning("⚠️ OPENAI_API_KEY: 未配置!")
    
    model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    logger.info(f"✓ 默认模型: {model}")
    
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🧠 Mindmap Service 已关闭")


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Mindmap Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

