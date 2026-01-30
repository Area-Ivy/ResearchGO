"""
Agent Service Main Entry
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

from .api.agent import router as agent_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ResearchGO Agent Service",
    description="AI Research Agent powered by LangGraph",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "agent-service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/agent/chat",
            "tools": "/api/agent/tools",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """健康检查端点 - 供 Traefik 等网关使用"""
    return {"status": "healthy", "service": "agent-service"}


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("=" * 60)
    logger.info("Starting ResearchGO Agent Service...")
    
    # 1. Register to Consul
    try:
        from .utils.consul_registry import register_service
        await register_service()
    except Exception as e:
        logger.warning(f"Consul registration failed (service will run standalone): {e}")
    
    # 2. Initialize Config Center
    try:
        from .utils.config_center import get_config_center
        config_center = get_config_center()
        
        # 从配置中心获取 OpenAI 模型配置
        model = await config_center.get("config/openai/model", os.getenv("OPENAI_MODEL", "gpt-4o"))
        logger.info(f"📦 Config Center:")
        logger.info(f"   - OpenAI Model: {model}")
        logger.info(f"   - Agent Timeout: {await config_center.get('config/agent/timeout', 120)}s")
        logger.info(f"   - Max Iterations: {await config_center.get('config/agent/max_iterations', 10)}")
    except Exception as e:
        logger.warning(f"Config Center initialization failed: {e}")
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # 3. Initialize Service Discovery
    try:
        from .utils.service_discovery import get_service_discovery
        sd = get_service_discovery()
        
        logger.info("📡 Service Discovery (动态发现):")
        logger.info(f"   - Auth: {await sd.auth_service()}")
        logger.info(f"   - Conversation: {await sd.conversation_service()}")
        logger.info(f"   - Vector Search: {await sd.vector_search_service()}")
        logger.info(f"   - Literature: {await sd.literature_service()}")
        logger.info(f"   - Analysis: {await sd.analysis_service()}")
    except Exception as e:
        logger.warning(f"Service Discovery initialization failed: {e}")
        # Fallback to environment variables
        logger.info("📡 Microservices URLs (环境变量回退):")
        logger.info(f"   - Auth: {os.getenv('AUTH_SERVICE_URL', 'http://localhost:8001')}")
        logger.info(f"   - Conversation: {os.getenv('CONVERSATION_SERVICE_URL', 'http://localhost:8002')}")
        logger.info(f"   - Vector Search: {os.getenv('VECTOR_SEARCH_SERVICE_URL', 'http://localhost:8004')}")
        logger.info(f"   - Literature: {os.getenv('LITERATURE_SERVICE_URL', 'http://localhost:8005')}")
    
    # Check OpenAI configuration
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  OPENAI_API_KEY is not set!")
    else:
        logger.info("✓ OPENAI_API_KEY is configured")
    
    logger.info(f"✓ Using model: {model}")
    
    # Initialize conversation cache with background writer
    from .memory.conversation_cache import init_conversation_cache
    await init_conversation_cache()
    logger.info("✓ Conversation cache initialized (Redis + background writer)")
    
    # Initialize agent
    from .agent.graph import get_agent
    agent = get_agent()
    logger.info(f"✓ Agent initialized with {len(agent.tools)} tools")
    
    # Log memory system configuration
    from .config import (
        ENABLE_CHECKPOINTER, ENABLE_CONVERSATION_SUMMARY, 
        ENABLE_SEMANTIC_MEMORY, SLIDING_WINDOW_SIZE
    )
    logger.info("🧠 Memory System:")
    logger.info(f"   - Redis Checkpointer: {'✓' if ENABLE_CHECKPOINTER else '✗'}")
    logger.info(f"   - Conversation Summary: {'✓' if ENABLE_CONVERSATION_SUMMARY else '✗'}")
    logger.info(f"   - Semantic Memory: {'✓' if ENABLE_SEMANTIC_MEMORY else '✗'}")
    logger.info(f"   - Sliding Window Size: {SLIDING_WINDOW_SIZE}")
    
    logger.info("=" * 60)
    logger.info("🤖 Agent Service is ready!")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down Agent Service...")
    
    # Deregister from Consul
    try:
        from .utils.consul_registry import deregister_service
        await deregister_service()
    except Exception as e:
        logger.warning(f"Consul deregistration failed: {e}")
    
    # Close conversation cache (flush pending writes)
    from .memory.conversation_cache import get_conversation_cache
    cache = get_conversation_cache()
    await cache.close()
    logger.info("✓ Conversation cache closed")
    
    # Close checkpointer
    from .memory.checkpointer import get_checkpointer
    checkpointer = get_checkpointer()
    if checkpointer:
        await checkpointer.close()
        logger.info("✓ Checkpointer closed")
    
    logger.info("Agent Service shutdown complete")

