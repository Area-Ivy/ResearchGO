"""
Milvus向量数据库服务
"""
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility
)
import logging
from app.database import MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION

logger = logging.getLogger(__name__)


class MilvusService:
    """Milvus向量数据库服务类"""
    
    def __init__(self):
        """初始化Milvus服务"""
        self.host = MILVUS_HOST
        self.port = MILVUS_PORT
        self.collection_name = MILVUS_COLLECTION
        self.collection: Optional[Collection] = None
        self._connected = False
        
    def connect(self) -> bool:
        """连接到Milvus数据库"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            self._connected = True
            logger.info(f"✓ Connected to Milvus: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}")
            self._connected = False
            return False
    
    def disconnect(self):
        """断开Milvus连接"""
        try:
            connections.disconnect("default")
            self._connected = False
            logger.info("Disconnected from Milvus")
        except Exception as e:
            logger.error(f"Error disconnecting from Milvus: {str(e)}")
    
    def drop_collection(self) -> bool:
        """删除向量集合（用于重建 schema）"""
        try:
            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                logger.info(f"✓ Dropped collection '{self.collection_name}'")
                self.collection = None
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to drop collection: {str(e)}")
            return False
    
    def create_collection(self, dim: int = 1536, force_recreate: bool = False) -> bool:
        """创建向量集合（如果不存在）"""
        try:
            if utility.has_collection(self.collection_name):
                if force_recreate:
                    logger.info(f"Force recreating collection '{self.collection_name}'...")
                    self.drop_collection()
                else:
                    logger.info(f"Collection '{self.collection_name}' already exists")
                    self.collection = Collection(self.collection_name)
                    return True
            
            # 定义字段
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="paper_id", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=300),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=1000),
                FieldSchema(name="file_name", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="chunk_chars", dtype=DataType.INT64),
                FieldSchema(name="page_range", dtype=DataType.VARCHAR, max_length=200),  # hierarchy_path 需要更长
                FieldSchema(name="upload_time", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=100),
            ]
            
            schema = CollectionSchema(fields=fields, description="Research papers collection")
            self.collection = Collection(name=self.collection_name, schema=schema)
            
            logger.info(f"✓ Created collection '{self.collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            return False
    
    def create_index(self) -> bool:
        """创建向量索引"""
        try:
            if not self.collection:
                logger.error("Collection not initialized")
                return False
            
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            
            self.collection.create_index(field_name="embedding", index_params=index_params)
            logger.info("✓ Created index on embedding field")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index: {str(e)}")
            return False
    
    def insert_vectors(
        self,
        paper_ids: List[str],
        chunk_ids: List[str],
        chunk_indices: List[int],
        embeddings: List[List[float]],
        titles: List[str],
        file_names: List[str],
        contents: List[str],
        chunk_chars: List[int],
        page_ranges: List[str],
        upload_times: List[str],
        sources: List[str]
    ) -> bool:
        """插入向量数据"""
        try:
            if not self.collection:
                logger.error("Collection not initialized")
                return False
            
            entities = [
                paper_ids, chunk_ids, chunk_indices, embeddings,
                titles, file_names, contents, chunk_chars,
                page_ranges, upload_times, sources
            ]
            
            self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"✓ Inserted {len(paper_ids)} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert vectors: {str(e)}")
            return False
    
    def search_similar(
        self,
        query_vectors: List[List[float]],
        top_k: int = 10,
        filter_expr: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """搜索相似向量"""
        try:
            if not self.collection:
                logger.error("Collection not initialized")
                return []
            
            self.collection.load()
            
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            
            search_kwargs = {
                "data": query_vectors,
                "anns_field": "embedding",
                "param": search_params,
                "limit": top_k,
                "output_fields": [
                    "paper_id", "chunk_id", "chunk_index",
                    "title", "file_name", "content", "chunk_chars",
                    "page_range", "upload_time", "source"
                ]
            }
            
            if filter_expr:
                search_kwargs["expr"] = filter_expr
            
            results = self.collection.search(**search_kwargs)
            
            formatted_results = []
            for hits in results:
                hits_list = []
                for hit in hits:
                    hits_list.append({
                        "id": hit.id,
                        "distance": hit.distance,
                        "relevance_score": 1 / (1 + hit.distance),
                        "paper_id": hit.entity.get("paper_id"),
                        "title": hit.entity.get("title"),
                        "file_name": hit.entity.get("file_name"),
                        "upload_time": hit.entity.get("upload_time"),
                        "chunk_id": hit.entity.get("chunk_id"),
                        "chunk_index": hit.entity.get("chunk_index"),
                        "content": hit.entity.get("content"),
                        "chunk_chars": hit.entity.get("chunk_chars"),
                        "page_range": hit.entity.get("page_range"),
                        "source": hit.entity.get("source")
                    })
                formatted_results.append(hits_list)
            
            logger.info(f"Search completed, returned {len(formatted_results)} result groups")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    def delete_by_paper_id(self, paper_ids: List[str]) -> bool:
        """根据论文ID删除向量"""
        import json
        try:
            if not self.collection:
                logger.error("Collection not initialized")
                return False
            
            # 使用 json.dumps 确保字符串用双引号（Milvus 要求）
            paper_ids_str = json.dumps(paper_ids)
            expr = f"paper_id in {paper_ids_str}"
            
            logger.info(f"Deleting vectors with expr: {expr}")
            
            # 先查询有多少条记录
            before_count = self.collection.query(expr=expr, output_fields=["paper_id"])
            logger.info(f"Found {len(before_count)} vectors to delete")
            
            if len(before_count) > 0:
                self.collection.delete(expr)
                # 刷新以确保删除生效
                self.collection.flush()
                logger.info(f"✓ Deleted {len(before_count)} vectors for papers: {paper_ids}")
            else:
                logger.warning(f"No vectors found for papers: {paper_ids}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            if not self.collection:
                return {}
            
            self.collection.flush()
            stats = self.collection.num_entities
            
            return {
                "collection_name": self.collection_name,
                "num_entities": stats,
                "is_loaded": utility.load_state(self.collection_name)
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {}


# 全局实例
_milvus_service = None


def get_milvus_service() -> MilvusService:
    """获取Milvus服务实例"""
    global _milvus_service
    if _milvus_service is None:
        _milvus_service = MilvusService()
        if _milvus_service.connect():
            _milvus_service.create_collection(dim=1536)  # text-embedding-3-small维度
            _milvus_service.create_index()
    return _milvus_service
