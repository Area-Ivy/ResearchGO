"""
Analysis API
论文分析相关的 API 端点
"""
import logging
from fastapi import APIRouter, HTTPException, status
from app.models.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import get_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/generate", response_model=AnalysisResponse)
async def generate_analysis(request: AnalysisRequest):
    """
    根据PDF文件生成论文分析报告
    
    - object_name: MinIO中的PDF文件对象名称
    - language: 语言（zh/en，默认zh）
    """
    try:
        logger.info(f"Generating analysis for: {request.object_name}")
        
        service = get_analysis_service()
        result = await service.generate_analysis(
            object_name=request.object_name,
            language=request.language
        )
        
        return AnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analysis: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        service = get_analysis_service()
        return {
            "status": "healthy",
            "service": "analysis-service"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "analysis-service",
            "error": str(e)
        }

