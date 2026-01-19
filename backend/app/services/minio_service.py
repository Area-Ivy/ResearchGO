"""
MinIO Service
处理文件上传、下载和管理
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, BinaryIO
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
        
        # 确保桶存在
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在，不存在则创建"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error checking/creating bucket: {e}")
            raise
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        file_name: str,
        content_type: str = "application/pdf",
        metadata: Optional[dict] = None
    ) -> dict:
        """
        上传文件到 MinIO
        
        Args:
            file_data: 文件二进制数据
            file_name: 文件名
            content_type: 文件类型
            metadata: 额外的元数据
            
        Returns:
            包含文件信息的字典
        """
        try:
            # 生成唯一的对象名称（添加时间戳避免重名）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_name = f"{timestamp}_{file_name}"
            
            # 读取文件大小
            file_data.seek(0, 2)  # 移动到文件末尾
            file_size = file_data.tell()
            file_data.seek(0)  # 重置到开头
            
            # 准备元数据
            file_metadata = {
                "original_name": file_name,
                "upload_time": datetime.now().isoformat(),
                "content_type": content_type
            }
            if metadata:
                file_metadata.update(metadata)
            
            # 上传文件
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
                metadata=file_metadata
            )
            
            logger.info(f"Uploaded file: {object_name} ({file_size} bytes)")
            
            return {
                "object_name": object_name,
                "original_name": file_name,
                "size": file_size,
                "content_type": content_type,
                "upload_time": file_metadata["upload_time"]
            }
            
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")
    
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
    
    async def list_files(self, prefix: str = "") -> List[dict]:
        """
        列出所有文件
        
        Args:
            prefix: 对象名称前缀（可选）
            
        Returns:
            文件信息列表
        """
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            
            files = []
            for obj in objects:
                # 获取详细信息
                try:
                    stat = self.client.stat_object(self.bucket_name, obj.object_name)
                    
                    file_info = {
                        "object_name": obj.object_name,
                        "original_name": stat.metadata.get("X-Amz-Meta-Original_name", obj.object_name),
                        "size": obj.size,
                        "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                        "content_type": stat.content_type,
                        "metadata": stat.metadata
                    }
                    files.append(file_info)
                except Exception as e:
                    logger.warning(f"Error getting stats for {obj.object_name}: {e}")
                    # 使用基本信息
                    files.append({
                        "object_name": obj.object_name,
                        "original_name": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                        "content_type": "application/octet-stream",
                        "metadata": {}
                    })
            
            logger.info(f"Listed {len(files)} files")
            
            return files
            
        except S3Error as e:
            logger.error(f"Error listing files: {e}")
            raise Exception(f"Failed to list files: {str(e)}")
    
    async def delete_file(self, object_name: str) -> bool:
        """
        删除文件
        
        Args:
            object_name: MinIO 中的对象名称
            
        Returns:
            是否删除成功
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted file: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting file {object_name}: {e}")
            raise Exception(f"Failed to delete file: {str(e)}")
    
    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """
        生成预签名 URL（用于临时访问）
        
        Args:
            object_name: 对象名称
            expires: 过期时间（秒）
            
        Returns:
            预签名 URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise Exception(f"Failed to generate URL: {str(e)}")

