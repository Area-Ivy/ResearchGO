"""
Mindmap API
思维导图相关的 API 端点
"""
import logging
from fastapi import APIRouter, HTTPException, status
from app.models.mindmap import MindmapGenerateRequest, MindmapGenerateResponse
from app.services.mindmap_service import get_mindmap_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mindmap", tags=["mindmap"])


@router.post("/generate", response_model=MindmapGenerateResponse)
async def generate_mindmap(request: MindmapGenerateRequest):
    """
    根据PDF文件生成思维导图
    
    - object_name: MinIO中的PDF文件对象名称
    - max_depth: 思维导图最大深度（默认3层）
    - language: 语言（zh/en，默认zh）
    """
    try:
        logger.info(f"Generating mindmap for: {request.object_name}")
        
        service = get_mindmap_service()
        result = await service.generate_mindmap(
            object_name=request.object_name,
            max_depth=request.max_depth,
            language=request.language
        )
        
        return MindmapGenerateResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating mindmap: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate mindmap: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        service = get_mindmap_service()
        return {
            "status": "healthy",
            "service": "mindmap-service"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "mindmap-service",
            "error": str(e)
        }

