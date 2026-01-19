"""
Papers API
文献管理相关的 API 端点
"""
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.papers import (
    PaperUploadResponse,
    PaperInfo,
    PaperListResponse,
    DeleteResponse
)
from app.services.minio_service import MinIOService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/papers", tags=["papers"])

# 服务实例（延迟初始化）
_minio_service = None


def get_minio_service():
    """获取或创建 MinIO 服务实例"""
    global _minio_service
    if _minio_service is None:
        _minio_service = MinIOService()
    return _minio_service


@router.post("/upload", response_model=PaperUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_paper(file: UploadFile = File(...)):
    """
    上传论文文件
    
    - 支持 PDF 文件
    - 文件会被存储到 MinIO
    - 返回文件信息
    """
    try:
        # 验证文件类型
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        logger.info(f"Uploading file: {file.filename}")
        
        # 上传到 MinIO
        service = get_minio_service()
        result = await service.upload_file(
            file_data=file.file,
            file_name=file.filename,
            content_type=file.content_type or "application/pdf"
        )
        
        return PaperUploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/list", response_model=PaperListResponse)
async def list_papers():
    """
    列出所有论文
    
    - 返回所有已上传的文件
    - 包含文件名、大小、上传时间等信息
    """
    try:
        logger.info("Listing papers")
        
        service = get_minio_service()
        files = await service.list_files()
        
        # 按上传时间降序排序
        files.sort(key=lambda x: x.get("last_modified", ""), reverse=True)
        
        papers = [PaperInfo(**file_info) for file_info in files]
        
        return PaperListResponse(
            total=len(papers),
            papers=papers
        )
        
    except Exception as e:
        logger.error(f"Error listing papers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list papers: {str(e)}"
        )


@router.get("/view/{object_name}")
async def view_paper(object_name: str):
    """
    在线查看论文文件（在浏览器中显示）
    
    - object_name: MinIO 中的对象名称
    - 返回文件流用于在线查看
    """
    try:
        logger.info(f"Viewing paper: {object_name}")
        
        service = get_minio_service()
        file_data, file_info = await service.download_file(object_name)
        
        # 获取原始文件名
        original_name = file_info.get("metadata", {}).get("X-Amz-Meta-Original_name", object_name)
        
        return StreamingResponse(
            file_data,
            media_type=file_info.get("content_type", "application/pdf"),
            headers={
                "Content-Disposition": f'inline; filename="{original_name}"'  # inline而不是attachment
            }
        )
        
    except Exception as e:
        logger.error(f"Error viewing paper {object_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper not found: {object_name}"
        )


@router.get("/download/{object_name}")
async def download_paper(object_name: str):
    """
    下载论文文件（下载到本地）
    
    - object_name: MinIO 中的对象名称
    - 返回文件流用于下载
    """
    try:
        logger.info(f"Downloading paper: {object_name}")
        
        service = get_minio_service()
        file_data, file_info = await service.download_file(object_name)
        
        # 获取原始文件名
        original_name = file_info.get("metadata", {}).get("X-Amz-Meta-Original_name", object_name)
        
        return StreamingResponse(
            file_data,
            media_type=file_info.get("content_type", "application/pdf"),
            headers={
                "Content-Disposition": f'attachment; filename="{original_name}"'  # attachment用于下载
            }
        )
        
    except Exception as e:
        logger.error(f"Error downloading paper {object_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper not found: {object_name}"
        )


@router.delete("/delete/{object_name}", response_model=DeleteResponse)
async def delete_paper(object_name: str):
    """
    删除论文文件
    
    - object_name: MinIO 中的对象名称
    """
    try:
        logger.info(f"Deleting paper: {object_name}")
        
        service = get_minio_service()
        success = await service.delete_file(object_name)
        
        return DeleteResponse(
            success=success,
            message="Paper deleted successfully",
            object_name=object_name
        )
        
    except Exception as e:
        logger.error(f"Error deleting paper {object_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete paper: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        service = get_minio_service()
        # 尝试列出文件以验证连接
        await service.list_files()
        return {
            "status": "healthy",
            "service": "papers",
            "minio": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "papers",
            "minio": "disconnected",
            "error": str(e)
        }

