from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import time

from app.api import chat_router, literature_router
from app.api import papers, mindmap, analysis, auth, conversations
from app.routers import milvus
from app.database import init_db

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
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(chat_router)
app.include_router(literature_router)
app.include_router(papers.router)
app.include_router(mindmap.router)
app.include_router(analysis.router)
app.include_router(milvus.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ResearchGO API",
        "version": "1.0.0",
        "status": "running",
        "features": ["auth", "chat", "literature_search", "paper_library", "mindmap", "analysis", "milvus"]
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
    
    logger.info("✓ Features: Auth, Chat, Literature Search (OpenAlex), Paper Library (MinIO), Mindmap, Milvus")
    
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

