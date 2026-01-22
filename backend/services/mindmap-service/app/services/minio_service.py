"""
MinIO Service
处理文件下载
"""
import os
import logging
from typing import Optional
from minio import Minio
from minio.error import S3Error
from io import BytesIO

logger = logging.getLogger(__name__)


class MinIOService:
    """MinIO 对象存储服务"""
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "research-papers")
        self.secure = os.getenv("MINIO_SECURE", "False").lower() == "true"
        
        # 初始化 MinIO 客户端
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        logger.info(f"✓ MinIO service initialized: {self.endpoint}/{self.bucket_name}")
    
    async def download_file(self, object_name: str) -> tuple[BytesIO, dict]:
        """
        下载文件
        
        Args:
            object_name: MinIO 中的对象名称
            
        Returns:
            (文件数据, 文件信息)
        """
        try:
            # 获取对象
            response = self.client.get_object(self.bucket_name, object_name)
            
            # 读取数据到内存
            file_data = BytesIO(response.read())
            
            # 获取对象信息
            stat = self.client.stat_object(self.bucket_name, object_name)
            
            file_info = {
                "object_name": object_name,
                "size": stat.size,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                "metadata": stat.metadata
            }
            
            response.close()
            response.release_conn()
            
            logger.info(f"Downloaded file: {object_name}")
            
            return file_data, file_info
            
        except S3Error as e:
            logger.error(f"Error downloading file {object_name}: {e}")
            raise Exception(f"Failed to download file: {str(e)}")


# 单例服务实例
_minio_service = None

def get_minio_service() -> MinIOService:
    """获取 MinIO 服务实例"""
    global _minio_service
    if _minio_service is None:
        _minio_service = MinIOService()
    return _minio_service

