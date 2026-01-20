"""
Milvus 向量数据库服务
提供向量存储、检索和管理功能
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
from loguru import logger
import os


class MilvusService:
    """Milvus 向量数据库服务类"""
    
    def __init__(
        self,
        host: str = None,
        port: str = None,
        collection_name: str = "research_papers"
    ):
        """
        初始化 Milvus 服务
        
        Args:
            host: Milvus 主机地址
            port: Milvus 端口
            collection_name: 集合名称
        """
        self.host = host or os.getenv("MILVUS_HOST", "localhost")
        self.port = port or os.getenv("MILVUS_PORT", "19530")
        self.collection_name = collection_name
        self.collection: Optional[Collection] = None
        self._connected = False
        
    def connect(self) -> bool:
        """
        连接到 Milvus 数据库
        
        Returns:
            bool: 连接是否成功
        """
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            self._connected = True
            logger.info(f"成功连接到 Milvus: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"连接 Milvus 失败: {str(e)}")
            self._connected = False
            return False
    
    def disconnect(self):
        """断开 Milvus 连接"""
        try:
            connections.disconnect("default")
            self._connected = False
            logger.info("已断开 Milvus 连接")
        except Exception as e:
            logger.error(f"断开 Milvus 连接失败: {str(e)}")
    
    def create_collection(
        self,
        dim: int = 768,
        description: str = "研究论文向量集合"
    ) -> bool:
        """
        创建向量集合
        
        Args:
            dim: 向量维度（默认 768，适用于大多数 BERT 模型）
            description: 集合描述
            
        Returns:
            bool: 创建是否成功
        """
        try:
            # 检查集合是否已存在
            if utility.has_collection(self.collection_name):
                logger.info(f"集合 '{self.collection_name}' 已存在")
                self.collection = Collection(self.collection_name)
                return True
            
            # 定义字段
            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=True,
                    description="主键ID"
                ),
                FieldSchema(
                    name="paper_id",
                    dtype=DataType.VARCHAR,
                    max_length=255,
                    description="论文ID（MinIO对象名）"
                ),
                FieldSchema(
                    name="chunk_id",
                    dtype=DataType.VARCHAR,
                    max_length=300,
                    description="Chunk ID（paper_id#chunk_index）"
                ),
                FieldSchema(
                    name="chunk_index",
                    dtype=DataType.INT64,
                    description="Chunk索引（0开始）"
                ),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=dim,
                    description="向量嵌入"
                ),
                FieldSchema(
                    name="title",
                    dtype=DataType.VARCHAR,
                    max_length=1000,
                    description="论文标题"
                ),
                FieldSchema(
                    name="file_name",
                    dtype=DataType.VARCHAR,
                    max_length=500,
                    description="原始文件名"
                ),
                FieldSchema(
                    name="content",
                    dtype=DataType.VARCHAR,
                    max_length=65535,
                    description="Chunk文本内容"
                ),
                FieldSchema(
                    name="chunk_chars",
                    dtype=DataType.INT64,
                    description="Chunk字符数"
                ),
                FieldSchema(
                    name="page_range",
                    dtype=DataType.VARCHAR,
                    max_length=50,
                    description="页码范围（如: 1-3）"
                ),
                FieldSchema(
                    name="upload_time",
                    dtype=DataType.VARCHAR,
                    max_length=50,
                    description="上传时间（ISO格式）"
                ),
                FieldSchema(
                    name="source",
                    dtype=DataType.VARCHAR,
                    max_length=100,
                    description="来源类型（chunk/full_text）"
                ),
            ]
            
            # 创建 schema
            schema = CollectionSchema(
                fields=fields,
                description=description
            )
            
            # 创建集合
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            
            logger.info(f"成功创建集合 '{self.collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"创建集合失败: {str(e)}")
            return False
    
    def create_index(
        self,
        index_type: str = "IVF_FLAT",
        metric_type: str = "L2",
        nlist: int = 1024
    ) -> bool:
        """
        创建向量索引
        
        Args:
            index_type: 索引类型（IVF_FLAT, IVF_SQ8, HNSW 等）
            metric_type: 距离度量类型（L2, IP, COSINE）
            nlist: IVF 索引的聚类中心数量
            
        Returns:
            bool: 创建是否成功
        """
        try:
            if not self.collection:
                logger.error("集合未初始化")
                return False
            
            # 定义索引参数
            index_params = {
                "metric_type": metric_type,
                "index_type": index_type,
                "params": {"nlist": nlist}
            }
            
            # 创建索引
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            logger.info(f"成功创建索引: {index_type}, {metric_type}")
            return True
            
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
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
        """
        插入向量数据（支持chunk和metadata）
        
        Args:
            paper_ids: 论文ID列表
            chunk_ids: Chunk ID列表
            chunk_indices: Chunk索引列表
            embeddings: 向量嵌入列表
            titles: 标题列表
            file_names: 原始文件名列表
            contents: 内容列表（chunk文本）
            chunk_chars: 字符数列表
            page_ranges: 页码范围列表
            upload_times: 上传时间列表
            sources: 来源列表
            
        Returns:
            bool: 插入是否成功
        """
        try:
            if not self.collection:
                logger.error("集合未初始化")
                return False
            
            # 构建实体数据（按schema字段顺序，不包括auto_id字段）
            entities = [
                paper_ids,
                chunk_ids,
                chunk_indices,
                embeddings,
                titles,
                file_names,
                contents,
                chunk_chars,
                page_ranges,
                upload_times,
                sources
            ]
            
            # 插入数据
            insert_result = self.collection.insert(entities)
            
            # 刷新数据到磁盘
            self.collection.flush()
            
            logger.info(f"成功插入 {len(paper_ids)} 条向量数据（chunks with metadata）")
            return True
            
        except Exception as e:
            logger.error(f"插入向量数据失败: {str(e)}")
            return False
    
    def search_similar(
        self,
        query_vectors: List[List[float]],
        top_k: int = 10,
        metric_type: str = "L2",
        search_params: Optional[Dict[str, Any]] = None,
        filter_expr: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        搜索相似向量
        
        Args:
            query_vectors: 查询向量列表
            top_k: 返回最相似的 top_k 个结果
            metric_type: 距离度量类型
            search_params: 搜索参数
            filter_expr: 过滤表达式（如: 'paper_id == "xxx"'）
            
        Returns:
            搜索结果列表
        """
        try:
            if not self.collection:
                logger.error("集合未初始化")
                return []
            
            # 加载集合到内存
            self.collection.load()
            
            # 设置默认搜索参数
            if search_params is None:
                search_params = {"metric_type": metric_type, "params": {"nprobe": 10}}
            
            # 执行搜索（返回所有metadata字段）
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
            
            # 如果有过滤表达式，添加到搜索参数
            if filter_expr:
                search_kwargs["expr"] = filter_expr
                logger.info(f"使用过滤表达式: {filter_expr}")
            
            results = self.collection.search(**search_kwargs)
            
            # 格式化结果（包含所有metadata）
            formatted_results = []
            for hits in results:
                hits_list = []
                for hit in hits:
                    hits_list.append({
                        "id": hit.id,
                        "distance": hit.distance,
                        "relevance_score": 1 / (1 + hit.distance),  # 转换为相关性分数
                        # Paper 基本信息
                        "paper_id": hit.entity.get("paper_id"),
                        "title": hit.entity.get("title"),
                        "file_name": hit.entity.get("file_name"),
                        "upload_time": hit.entity.get("upload_time"),
                        # Chunk 信息
                        "chunk_id": hit.entity.get("chunk_id"),
                        "chunk_index": hit.entity.get("chunk_index"),
                        "content": hit.entity.get("content"),
                        "chunk_chars": hit.entity.get("chunk_chars"),
                        "page_range": hit.entity.get("page_range"),
                        "source": hit.entity.get("source")
                    })
                formatted_results.append(hits_list)
            
            logger.info(f"搜索完成，返回 {len(formatted_results)} 组结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索向量失败: {str(e)}")
            return []
    
    def delete_by_paper_id(self, paper_ids: List[str]) -> bool:
        """
        根据论文ID删除向量
        
        Args:
            paper_ids: 论文ID列表
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if not self.collection:
                logger.error("集合未初始化")
                return False
            
            # 构建删除表达式
            expr = f"paper_id in {paper_ids}"
            
            # 执行删除
            self.collection.delete(expr)
            
            logger.info(f"成功删除 {len(paper_ids)} 条向量数据")
            return True
            
        except Exception as e:
            logger.error(f"删除向量数据失败: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Returns:
            统计信息字典
        """
        try:
            if not self.collection:
                logger.error("集合未初始化")
                return {}
            
            self.collection.flush()
            stats = self.collection.num_entities
            
            return {
                "collection_name": self.collection_name,
                "num_entities": stats,
                "is_loaded": utility.load_state(self.collection_name)
            }
            
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {str(e)}")
            return {}
    
    def drop_collection(self) -> bool:
        """
        删除集合（谨慎使用！）
        
        Returns:
            bool: 删除是否成功
        """
        try:
            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                self.collection = None
                logger.warning(f"已删除集合 '{self.collection_name}'")
                return True
            else:
                logger.info(f"集合 '{self.collection_name}' 不存在")
                return False
                
        except Exception as e:
            logger.error(f"删除集合失败: {str(e)}")
            return False


# 创建全局实例
milvus_service = MilvusService()

