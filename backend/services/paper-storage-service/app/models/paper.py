"""
论文模型
"""
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text
from sqlalchemy.sql import func
from app.database import Base


class Paper(Base):
    """论文表 - 存储论文元数据"""
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)  # 上传者ID
    object_name = Column(String(500), unique=True, nullable=False, index=True)  # MinIO对象名
    original_name = Column(String(500), nullable=False)  # 原始文件名
    file_size = Column(BigInteger, nullable=False)  # 文件大小（字节）
    content_type = Column(String(100), default="application/pdf")  # 文件类型
    title = Column(String(500))  # 论文标题（可选，后续可以从PDF提取）
    authors = Column(Text)  # 作者（可选）
    year = Column(Integer)  # 年份（可选）
    abstract = Column(Text)  # 摘要（可选）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Paper(id={self.id}, name='{self.original_name}', user_id={self.user_id})>"

