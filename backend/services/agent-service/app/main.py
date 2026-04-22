"""Agent service main entry."""
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.agent import router as agent_router

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ResearchGO Agent Service",
    description="AI Research Agent powered by LangGraph",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)


@app.get("/")
async def root():
    return {
        "service": "agent-service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {"chat": "/api/agent/chat", "tools": "/api/agent/tools", "health": "/health"},
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agent-service"}


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Starting ResearchGO Agent Service...")

    try:
        from .utils.consul_registry import register_service
        await register_service()
    except Exception as exc:
        logger.warning("Consul registration failed (service will run standalone): %s", exc)

    try:
        from .utils.config_center import get_config_center

        config_center = get_config_center()
        model = await config_center.get("config/openai/model", os.getenv("OPENAI_MODEL", "gpt-4o"))
        logger.info("Config Center:")
        logger.info("   - OpenAI Model: %s", model)
        logger.info("   - Agent Timeout: %ss", await config_center.get("config/agent/timeout", 120))
        logger.info("   - Max Iterations: %s", await config_center.get("config/agent/max_iterations", 10))
    except Exception as exc:
        logger.warning("Config Center initialization failed: %s", exc)
        model = os.getenv("OPENAI_MODEL", "gpt-4o")

    try:
        from .utils.service_discovery import get_service_discovery

        sd = get_service_discovery()
        logger.info("Service Discovery:")
        logger.info("   - Auth: %s", await sd.auth_service())
        logger.info("   - Conversation: %s", await sd.conversation_service())
        logger.info("   - Vector Search: %s", await sd.vector_search_service())
        logger.info("   - Literature: %s", await sd.literature_service())
        logger.info("   - Analysis: %s", await sd.analysis_service())
        logger.info("   - MCP: %s", await sd.mcp_service())
    except Exception as exc:
        logger.warning("Service Discovery initialization failed: %s", exc)

    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY is not set")
    else:
        logger.info("OPENAI_API_KEY is configured")
    logger.info("Using model: %s", model)

    from .memory.conversation_cache import init_conversation_cache

    await init_conversation_cache()
    logger.info("Conversation cache initialized (Redis + background writer)")

    from .agent.graph import get_agent

    agent = get_agent()
    try:
        await agent.refresh_tools(force=True)
    except Exception as exc:
        logger.warning("Initial MCP tool refresh failed: %s", exc)
    logger.info("Agent initialized with %s tools", len(agent.tools))

    from .config import ENABLE_CHECKPOINTER, ENABLE_CONVERSATION_SUMMARY, ENABLE_SEMANTIC_MEMORY, SLIDING_WINDOW_SIZE

    logger.info("Memory System:")
    logger.info("   - Redis Checkpointer: %s", ENABLE_CHECKPOINTER)
    logger.info("   - Conversation Summary: %s", ENABLE_CONVERSATION_SUMMARY)
    logger.info("   - Semantic Memory: %s", ENABLE_SEMANTIC_MEMORY)
    logger.info("   - Sliding Window Size: %s", SLIDING_WINDOW_SIZE)
    logger.info("Agent Service is ready")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Agent Service...")
    try:
        from .utils.consul_registry import deregister_service
        await deregister_service()
    except Exception as exc:
        logger.warning("Consul deregistration failed: %s", exc)

    from .memory.conversation_cache import get_conversation_cache

    cache = get_conversation_cache()
    await cache.close()
    logger.info("Conversation cache closed")

    from .memory.checkpointer import get_checkpointer

    checkpointer = get_checkpointer()
    if checkpointer:
        await checkpointer.close()
        logger.info("Checkpointer closed")

    logger.info("Agent Service shutdown complete")
