import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .api.mcp import router as mcp_router

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="ResearchGO MCP Server", version="1.0.0", description="MCP-compatible tool server for ResearchGO")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(mcp_router)


@app.get("/")
async def root():
    return {"service": "research-mcp-server", "status": "running", "endpoint": "/mcp"}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "research-mcp-server"}


@app.on_event("startup")
async def startup_event():
    logger.info("Starting ResearchGO MCP Server...")
    try:
        from .utils.consul_registry import register_service
        await register_service()
    except Exception as exc:
        logger.warning("Consul registration failed (service will run standalone): %s", exc)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down ResearchGO MCP Server...")
    try:
        from .utils.consul_registry import deregister_service
        await deregister_service()
    except Exception as exc:
        logger.warning("Consul deregistration failed: %s", exc)
