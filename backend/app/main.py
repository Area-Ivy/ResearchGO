from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import time

from app.api import papers, conversations
# 注意：chat_router 已迁移到聊天服务 (localhost:8006)
# 注意：literature_router 已迁移到文献检索服务 (localhost:8005)
# 注意：mindmap 已迁移到思维导图服务 (localhost:8007)
# 注意：analysis 已迁移到分析服务 (localhost:8008)
from app.routers import milvus
from app.database import init_db

# 注意：认证功能已迁移到认证服务 (localhost:8001)

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
    title="ResearchGO API",
    description="AI-powered research assistant API with chat and literature search",
    version="1.0.0"
)

# Configure CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
    max_age=3600,
)

# Keep for logging purposes
allowed_origins_str = os.getenv('ALLOWED_ORIGINS', '*')
allowed_origins = ["*"] if allowed_origins_str == "*" else [origin.strip() for origin in allowed_origins_str.split(',')]

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for debugging"""
    start_time = time.time()
    
    # Log request details
    logger.info(f"📨 {request.method} {request.url.path}")
    logger.info(f"   Origin: {request.headers.get('origin', 'N/A')}")
    logger.info(f"   Content-Type: {request.headers.get('content-type', 'N/A')}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"✓ {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
    
    return response

# Include routers
# app.include_router(auth.router)  # 已迁移到认证服务 (localhost:8001)
# app.include_router(conversations.router)  # 已迁移到对话服务 (localhost:8002)
# app.include_router(papers.router)  # 已迁移到论文存储服务 (localhost:8003)
# app.include_router(milvus.router)  # 已迁移到向量搜索服务 (localhost:8004)
# app.include_router(literature_router)  # 已迁移到文献检索服务 (localhost:8005)
# app.include_router(chat_router)  # 已迁移到聊天服务 (localhost:8006)
# app.include_router(mindmap.router)  # 已迁移到思维导图服务 (localhost:8007)
# app.include_router(analysis.router)  # 已迁移到分析服务 (localhost:8008)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ResearchGO API",
        "version": "1.0.0",
        "status": "running",
        "features": [],
        "note": "所有功能已迁移到独立微服务",
        "auth_service": "http://localhost:8001",
        "conversation_service": "http://localhost:8002",
        "paper_storage_service": "http://localhost:8003",
        "vector_search_service": "http://localhost:8004",
        "literature_search_service": "http://localhost:8005",
        "chat_service": "http://localhost:8006",
        "mindmap_service": "http://localhost:8007",
        "analysis_service": "http://localhost:8008"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "chat-api"
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("=" * 60)
    logger.info("Starting ResearchGO API...")
    logger.info("🌐 CORS: Allowing ALL origins (*)")
    logger.info("   Methods: ALL (*)")
    logger.info("   Headers: ALL (*)")
    
    # Initialize database
    try:
        init_db()
        logger.info("✓ Database initialized successfully")
    except Exception as e:
        logger.error(f"⚠️  Failed to initialize database: {e}")
    
    # Check for required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("⚠️  OPENAI_API_KEY is not set!")
    else:
        logger.info("✓ OPENAI_API_KEY is configured")
    
    model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    logger.info(f"✓ Using model: {model}")
    
    contact_email = os.getenv('CONTACT_EMAIL', 'Not set')
    logger.info(f"📧 Contact email for OpenAlex: {contact_email}")
    
    logger.info("✓ 所有功能已迁移到独立微服务")
    logger.info("🔐 Auth Service: http://localhost:8001 (独立认证服务)")
    logger.info("💬 Conversation Service: http://localhost:8002 (独立对话服务)")
    logger.info("📄 Paper Storage Service: http://localhost:8003 (独立论文存储服务)")
    logger.info("🔍 Vector Search Service: http://localhost:8004 (独立向量搜索服务)")
    logger.info("📚 Literature Search Service: http://localhost:8005 (独立文献检索服务)")
    logger.info("🤖 Chat Service: http://localhost:8006 (独立聊天服务)")
    logger.info("🧠 Mindmap Service: http://localhost:8007 (独立思维导图服务)")
    logger.info("📊 Analysis Service: http://localhost:8008 (独立分析服务)")
    
    # Check MinIO configuration
    minio_endpoint = os.getenv('MINIO_ENDPOINT', 'Not set')
    logger.info(f"📦 MinIO endpoint: {minio_endpoint}")
    
    # Check MySQL configuration
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_database = os.getenv('MYSQL_DATABASE', 'researchgo')
    logger.info(f"🗄️  MySQL: {mysql_host}/{mysql_database}")
    
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down ResearchGO API...")

