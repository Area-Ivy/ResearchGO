"""
向量搜索服务 - 主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.api import search
from app.services.milvus_service import get_milvus_service
from app.services.openai_service import get_openai_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="向量搜索服务",
    description="基于Milvus和OpenAI的语义搜索和问答服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(search.router)


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("=" * 60)
    logger.info("🚀 向量搜索服务启动中...")
    logger.info("=" * 60)
    
    # Register to Consul
    try:
        from app.utils.consul_registry import register_service
        await register_service()
    except Exception as e:
        logger.warning(f"Consul registration failed: {e}")
    
    # 初始化Milvus服务
    try:
        milvus_service = get_milvus_service()
        logger.info("✅ Milvus服务初始化成功")
    except Exception as e:
        logger.error(f"❌ Milvus服务初始化失败: {e}")
    
    # 初始化OpenAI服务
    try:
        openai_service = get_openai_service()
        logger.info("✅ OpenAI服务初始化成功")
    except Exception as e:
        logger.error(f"❌ OpenAI服务初始化失败: {e}")
    
    logger.info("=" * 60)
    logger.info("✓ 向量搜索服务已启动")
    logger.info(f"✓ 端口: 8004")
    logger.info(f"✓ API文档: http://localhost:8004/docs")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    # Deregister from Consul
    try:
        from app.utils.consul_registry import deregister_service
        await deregister_service()
    except Exception as e:
        logger.warning(f"Consul deregistration failed: {e}")
    
    logger.info("向量搜索服务已关闭")


@app.get("/")
async def root():
    """根路由"""
    return {
        "service": "vector-search-service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "semantic_search": "/api/vector/search",
            "paper_qa": "/api/vector/qa",
            "index_paper": "/api/vector/index",
            "delete_vectors": "/api/vector/delete/{paper_id}",
            "stats": "/api/vector/stats",
            "health": "/api/vector/health"
        }
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "vector-search-service"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

