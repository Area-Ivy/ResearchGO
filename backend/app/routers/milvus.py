"""
Milvus 向量数据库管理 API
提供集合管理、向量操作等功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.services.milvus_service import milvus_service
from pymilvus import utility, connections
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/milvus", tags=["milvus"])


class CreateCollectionRequest(BaseModel):
    """创建集合请求"""
    name: str
    description: Optional[str] = ""
    dimension: int = 768


class CollectionResponse(BaseModel):
    """集合响应"""
    name: str
    description: Optional[str]
    num_entities: int
    dimension: Optional[int]
    index_type: Optional[str]
    loaded: bool


@router.get("/status")
async def get_status():
    """
    获取 Milvus 连接状态
    """
    try:
        is_connected = milvus_service._connected
        if not is_connected:
            # 尝试重新连接
            is_connected = milvus_service.connect()
        
        return {
            "connected": is_connected,
            "host": milvus_service.host,
            "port": milvus_service.port
        }
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return {
            "connected": False,
            "host": milvus_service.host,
            "port": milvus_service.port,
            "error": str(e)
        }


@router.get("/collections")
async def list_collections():
    """
    获取所有集合列表
    """
    try:
        # 确保已连接
        if not milvus_service._connected:
            milvus_service.connect()
        
        # 获取所有集合名称
        collection_names = utility.list_collections()
        
        collections = []
        for name in collection_names:
            try:
                from pymilvus import Collection
                collection = Collection(name)
                
                # 获取集合信息
                collection.flush()
                num_entities = collection.num_entities
                
                # 获取 schema 信息
                schema = collection.schema
                dimension = None
                for field in schema.fields:
                    if field.dtype.name.startswith('FLOAT_VECTOR') or field.dtype.name.startswith('BINARY_VECTOR'):
                        dimension = field.params.get('dim')
                        break
                
                # 获取索引信息
                index_type = None
                try:
                    indexes = collection.indexes
                    if indexes:
                        index_type = indexes[0].params.get('index_type', 'Unknown')
                except:
                    pass
                
                # 检查是否已加载
                loaded = False
                try:
                    loaded_state = utility.load_state(name)
                    loaded = str(loaded_state).lower() == 'loaded'
                except:
                    pass
                
                collections.append({
                    "name": name,
                    "description": schema.description or "",
                    "num_entities": num_entities,
                    "dimension": dimension,
                    "index_type": index_type,
                    "loaded": loaded
                })
            except Exception as e:
                logger.error(f"Failed to get info for collection {name}: {e}")
                # 仍然添加基本信息
                collections.append({
                    "name": name,
                    "description": "",
                    "num_entities": 0,
                    "dimension": None,
                    "index_type": None,
                    "loaded": False
                })
        
        return {"collections": collections}
    
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections")
async def create_collection(request: CreateCollectionRequest):
    """
    创建新集合
    """
    try:
        # 确保已连接
        if not milvus_service._connected:
            milvus_service.connect()
        
        # 检查集合是否已存在
        if utility.has_collection(request.name):
            raise HTTPException(status_code=400, detail="Collection already exists")
        
        # 创建集合
        from pymilvus import Collection, FieldSchema, CollectionSchema, DataType
        
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="paper_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=request.dimension),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="abstract", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=100),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description=request.description or f"Collection with {request.dimension}D vectors"
        )
        
        collection = Collection(name=request.name, schema=schema)
        
        # 创建索引
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        
        return {
            "success": True,
            "message": f"Collection '{request.name}' created successfully",
            "collection": {
                "name": request.name,
                "description": request.description,
                "dimension": request.dimension
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """
    删除集合
    """
    try:
        # 确保已连接
        if not milvus_service._connected:
            milvus_service.connect()
        
        # 检查集合是否存在
        if not utility.has_collection(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # 删除集合
        utility.drop_collection(collection_name)
        
        return {
            "success": True,
            "message": f"Collection '{collection_name}' deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/load")
async def load_collection(collection_name: str):
    """
    加载集合到内存
    """
    try:
        # 确保已连接
        if not milvus_service._connected:
            milvus_service.connect()
        
        # 检查集合是否存在
        if not utility.has_collection(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")
        
        from pymilvus import Collection
        collection = Collection(collection_name)
        collection.load()
        
        return {
            "success": True,
            "message": f"Collection '{collection_name}' loaded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/release")
async def release_collection(collection_name: str):
    """
    释放集合从内存
    """
    try:
        # 确保已连接
        if not milvus_service._connected:
            milvus_service.connect()
        
        # 检查集合是否存在
        if not utility.has_collection(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")
        
        from pymilvus import Collection
        collection = Collection(collection_name)
        collection.release()
        
        return {
            "success": True,
            "message": f"Collection '{collection_name}' released successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to release collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}")
async def get_collection_info(collection_name: str):
    """
    获取集合详细信息
    """
    try:
        # 确保已连接
        if not milvus_service._connected:
            milvus_service.connect()
        
        # 检查集合是否存在
        if not utility.has_collection(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")
        
        from pymilvus import Collection
        collection = Collection(collection_name)
        
        # 获取基本信息
        collection.flush()
        num_entities = collection.num_entities
        schema = collection.schema
        
        # 获取字段信息
        fields_info = []
        dimension = None
        for field in schema.fields:
            field_info = {
                "name": field.name,
                "type": field.dtype.name,
                "is_primary": field.is_primary,
                "auto_id": field.auto_id if hasattr(field, 'auto_id') else None
            }
            
            if field.dtype.name.startswith('FLOAT_VECTOR') or field.dtype.name.startswith('BINARY_VECTOR'):
                dimension = field.params.get('dim')
                field_info['dimension'] = dimension
            elif field.dtype.name == 'VARCHAR':
                field_info['max_length'] = field.params.get('max_length')
            
            fields_info.append(field_info)
        
        # 获取索引信息
        indexes_info = []
        try:
            indexes = collection.indexes
            for index in indexes:
                indexes_info.append({
                    "field_name": index.field_name,
                    "index_type": index.params.get('index_type'),
                    "metric_type": index.params.get('metric_type'),
                    "params": index.params.get('params', {})
                })
        except:
            pass
        
        # 检查加载状态
        loaded = False
        try:
            loaded_state = utility.load_state(collection_name)
            loaded = str(loaded_state).lower() == 'loaded'
        except:
            pass
        
        return {
            "name": collection_name,
            "description": schema.description or "",
            "num_entities": num_entities,
            "dimension": dimension,
            "fields": fields_info,
            "indexes": indexes_info,
            "loaded": loaded
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

