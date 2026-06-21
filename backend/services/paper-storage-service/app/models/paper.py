"""
Paper metadata model.
"""
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    object_name = Column(String(500), unique=True, nullable=False, index=True)
    original_name = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(100), default="application/pdf")
    title = Column(String(500))
    authors = Column(Text)
    year = Column(Integer)
    abstract = Column(Text)
    processing_status = Column(String(50), nullable=False, default="uploaded")
    processing_error = Column(Text)
    indexed_at = Column(DateTime)
    chunks_created = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (
            f"<Paper(id={self.id}, object_name='{self.object_name}', "
            f"user_id={self.user_id}, status='{self.processing_status}')>"
        )
