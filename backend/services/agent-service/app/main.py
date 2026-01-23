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
            "health": "/api/agent/health"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("=" * 60)
    logger.info("Starting ResearchGO Agent Service...")
    
    # Check OpenAI configuration
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  OPENAI_API_KEY is not set!")
    else:
        logger.info("✓ OPENAI_API_KEY is configured")
    
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    logger.info(f"✓ Using model: {model}")
    
    # Log microservices configuration
    logger.info("📡 Microservices URLs:")
    logger.info(f"   - Auth: {os.getenv('AUTH_SERVICE_URL', 'http://localhost:8001')}")
    logger.info(f"   - Conversation: {os.getenv('CONVERSATION_SERVICE_URL', 'http://localhost:8002')}")
    logger.info(f"   - Paper Storage: {os.getenv('PAPER_STORAGE_SERVICE_URL', 'http://localhost:8003')}")
    logger.info(f"   - Vector Search: {os.getenv('VECTOR_SEARCH_SERVICE_URL', 'http://localhost:8004')}")
    logger.info(f"   - Literature: {os.getenv('LITERATURE_SERVICE_URL', 'http://localhost:8005')}")
    logger.info(f"   - Chat: {os.getenv('CHAT_SERVICE_URL', 'http://localhost:8006')}")
    logger.info(f"   - Mindmap: {os.getenv('MINDMAP_SERVICE_URL', 'http://localhost:8007')}")
    logger.info(f"   - Analysis: {os.getenv('ANALYSIS_SERVICE_URL', 'http://localhost:8008')}")
    
    # Initialize agent
    from .agent.graph import get_agent
    agent = get_agent()
    logger.info(f"✓ Agent initialized with {len(agent.tools)} tools")
    
    logger.info("=" * 60)
    logger.info("🤖 Agent Service is ready!")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down Agent Service...")

