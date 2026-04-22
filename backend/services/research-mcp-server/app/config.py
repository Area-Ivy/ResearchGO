import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "research-mcp-server")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8010"))
MCP_PROTOCOL_VERSION = os.getenv("MCP_PROTOCOL_VERSION", "2025-03-26")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
PAPER_STORAGE_SERVICE_URL = os.getenv("PAPER_STORAGE_SERVICE_URL", "http://localhost:8003")
VECTOR_SEARCH_SERVICE_URL = os.getenv("VECTOR_SEARCH_SERVICE_URL", "http://localhost:8004")
LITERATURE_SERVICE_URL = os.getenv("LITERATURE_SERVICE_URL", "http://localhost:8005")
MINDMAP_SERVICE_URL = os.getenv("MINDMAP_SERVICE_URL", "http://localhost:8007")
ANALYSIS_SERVICE_URL = os.getenv("ANALYSIS_SERVICE_URL", "http://localhost:8008")
