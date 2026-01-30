"""
论文存储API
"""
import logging
import os
import io
import httpx
import pdfplumber
from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from minio.error import S3Error

# 加载环境变量
load_dotenv()

from app.database import get_db
from app.models.paper import Paper
from app.schemas.paper import PaperUploadResponse, PaperListResponse, PaperInfo, DeleteResponse
from app.utils.auth_client import get_current_user
from app.utils.minio_client import get_minio_client, ensure_bucket_exists, MINIO_BUCKET

logger = logging.getLogger(__name__)

# 向量搜索服务URL
VECTOR_SEARCH_SERVICE_URL = os.getenv("VECTOR_SEARCH_SERVICE_URL", "http://localhost:8004")

# 打印SECRET_KEY前几位用于调试（不打印完整值）
_sk = os.getenv("SECRET_KEY", "")
logger.info(f"SECRET_KEY loaded: {_sk[:10]}..." if len(_sk) > 10 else "SECRET_KEY not set or too short!")


async def extract_text_from_pdf(pdf_data: bytes, max_pages: int = 50) -> str:
    """从PDF中提取文本"""
    try:
        text_content = []
        pdf_stream = io.BytesIO(pdf_data)
        
        with pdfplumber.open(pdf_stream) as pdf:
            total_pages = len(pdf.pages)
            pages_to_extract = min(total_pages, max_pages)
            
            logger.info(f"Extracting text from {pages_to_extract} pages (total: {total_pages})")
            
            for i, page in enumerate(pdf.pages[:pages_to_extract]):
                try:
                    text = page.extract_text()
                    if text:
                        text_content.append(f"--- Page {i+1} ---\n{text}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i+1}: {e}")
                    continue
        
        full_text = "\n\n".join(text_content)
        logger.info(f"Extracted {len(full_text)} characters from PDF")
        return full_text.strip()
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""


async def index_paper_to_vector_db(
    paper_id: str,
    title: str,
    file_name: str,
    pdf_content: bytes,
    token: str,
    use_structured: bool = True
):
    """
    将论文索引到向量数据库（后台任务）
    
    Args:
        paper_id: 论文ID
        title: 论文标题
        file_name: 文件名
        pdf_content: PDF二进制内容
        token: 认证令牌
        use_structured: 是否使用结构化解析（LLM 结构解析 + 递归语义切分）
    """
    try:
        logger.info(f"Indexing paper: {paper_id} (structured={use_structured})")
        
        # 提取PDF文本
        content = await extract_text_from_pdf(pdf_content)
        
        if not content or len(content) < 100:
            logger.warning(f"Insufficient content extracted from {paper_id}, skipping indexing")
            return
        
        index_request = {
            "paper_id": paper_id,
            "title": title,
            "file_name": file_name,
            "max_chunk_size": 1000,
        }
        
        if use_structured:
            # 结构化模式：LLM 解析 + 递归语义切分
            try:
                from app.utils.paper_structure_parser import get_paper_structure_parser
                from app.utils.recursive_semantic_chunker import chunk_structured_paper
                
                logger.info("Step 1: LLM 结构解析...")
                parser = get_paper_structure_parser()
                paper_structure = await parser.parse_structure(content)
                
                logger.info("Step 2: 递归语义切分...")
                structured_chunks = chunk_structured_paper(
                    paper_structure=paper_structure.to_dict(),
                    max_chunk_size=1000,
                    min_chunk_size=100,
                    chunk_overlap=100
                )
                
                # 构建结构化索引请求
                index_request["structured_chunks"] = [
                    {
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "section_type": chunk.section_type,
                        "section_title": chunk.section_title,
                        "subsection_title": chunk.subsection_title,
                        "hierarchy_path": chunk.hierarchy_path,
                        "char_count": chunk.char_count,
                        "is_complete_section": chunk.is_complete_section,
                        "metadata": {}
                    }
                    for chunk in structured_chunks
                ]
                index_request["paper_metadata"] = {
                    "title": paper_structure.title,
                    "authors": paper_structure.authors,
                    "abstract": paper_structure.abstract[:500] if paper_structure.abstract else "",
                    "references_count": paper_structure.references_count
                }
                
                logger.info(f"✓ 结构化解析完成: {len(structured_chunks)} chunks")
                
            except Exception as e:
                logger.warning(f"结构化解析失败，回退到简单模式: {e}")
                index_request["content"] = content
        else:
            # 简单模式
            index_request["content"] = content
        
        # 调用向量搜索服务的索引API
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{VECTOR_SEARCH_SERVICE_URL}/api/vector/index",
                json=index_request,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✓ Paper indexed successfully: {paper_id}")
                logger.info(f"  - Chunks: {result.get('chunks_created', 0)}")
                if result.get('section_types'):
                    logger.info(f"  - Section types: {result.get('section_types')}")
            else:
                logger.error(f"Failed to index paper {paper_id}: {response.status_code} - {response.text}")
                
    except Exception as e:
        logger.error(f"Error indexing paper {paper_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

router = APIRouter(prefix="/api/papers", tags=["论文存储"])


@router.post("/upload", response_model=PaperUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_paper(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传论文PDF文件（自动索引到向量数据库）"""
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    
    # 验证文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持PDF文件"
        )
    
    try:
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 生成唯一的对象名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"{timestamp}_{file.filename}"
        
        # 上传到MinIO
        client = get_minio_client()
        ensure_bucket_exists(client, MINIO_BUCKET)
        
        from io import BytesIO
        client.put_object(
            MINIO_BUCKET,
            object_name,
            BytesIO(file_content),
            length=file_size,
            content_type=file.content_type or "application/pdf"
        )
        
        # 保存元数据到数据库
        paper = Paper(
            user_id=current_user["id"],
            object_name=object_name,
            original_name=file.filename,
            file_size=file_size,
            content_type=file.content_type or "application/pdf"
        )
        
        db.add(paper)
        db.commit()
        db.refresh(paper)
        
        logger.info(f"Paper uploaded: {object_name} by user {current_user['id']}")
        
        # 后台任务：索引到向量数据库
        # 生成一个有效的token来调用向量搜索服务
        from jose import jwt
        from datetime import timedelta
        
        SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
        expire = datetime.utcnow() + timedelta(hours=1)
        token_data = {
            "sub": current_user["username"],
            "user_id": current_user["id"],
            "is_active": current_user.get("is_active", True),
            "is_superuser": current_user.get("is_superuser", False),
            "exp": expire
        }
        temp_token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        
        # 启动后台索引任务（使用同步方式）
        if background_tasks:
            def sync_index_task():
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(index_paper_to_vector_db(
                        paper_id=object_name,
                        title=file.filename.replace('.pdf', ''),
                        file_name=file.filename,
                        pdf_content=file_content,
                        token=temp_token
                    ))
                    loop.close()
                except Exception as e:
                    logger.error(f"Background indexing failed: {e}")
            
            background_tasks.add_task(sync_index_task)
            logger.info(f"Background indexing task started for: {object_name}")
        
        return PaperUploadResponse(
            object_name=object_name,
            original_name=file.filename,
            size=file_size,
            content_type=file.content_type or "application/pdf",
            upload_time=paper.created_at.isoformat()
        )
        
    except S3Error as e:
        logger.error(f"MinIO error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )


@router.get("/list", response_model=PaperListResponse)
async def list_papers(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的论文列表"""
    try:
        # 查询总数
        total = db.query(Paper).filter(Paper.user_id == current_user["id"]).count()
        
        # 查询论文列表
        papers = db.query(Paper).filter(
            Paper.user_id == current_user["id"]
        ).order_by(Paper.created_at.desc()).offset(skip).limit(limit).all()
        
        return PaperListResponse(
            total=total,
            papers=[PaperInfo.from_orm(p) for p in papers]
        )
        
    except Exception as e:
        logger.error(f"List papers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取列表失败: {str(e)}"
        )


@router.get("/download/{object_name}")
async def download_paper(
    object_name: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载论文文件"""
    try:
        # 验证权限
        paper = db.query(Paper).filter(
            Paper.object_name == object_name,
            Paper.user_id == current_user["id"]
        ).first()
        
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="论文不存在或无权访问"
            )
        
        # 从MinIO下载
        client = get_minio_client()
        response = client.get_object(MINIO_BUCKET, object_name)
        
        return StreamingResponse(
            response.stream(32*1024),  # 32KB chunks
            media_type=paper.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{paper.original_name}"'
            }
        )
        
    except S3Error as e:
        logger.error(f"MinIO download error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载失败: {str(e)}"
        )


@router.get("/view/{object_name}")
async def view_paper(
    object_name: str,
    token: str = None,  # iframe无法发送header，需要通过URL参数传递token
    db: Session = Depends(get_db)
):
    """在线预览论文 - 返回PDF文件供浏览器显示（支持iframe）"""
    from jose import jwt, JWTError
    import os
    
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM = "HS256"
    
    try:
        # 验证token
        if not token:
            raise HTTPException(status_code=401, detail="需要token参数")
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=403, detail="无效的token")
        except JWTError as e:
            logger.error(f"Token验证失败: {e}")
            raise HTTPException(status_code=403, detail="token验证失败")
        
        # 验证权限
        paper = db.query(Paper).filter(
            Paper.object_name == object_name,
            Paper.user_id == user_id
        ).first()
        
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="论文不存在或无权访问"
            )
        
        # 从MinIO获取文件
        client = get_minio_client()
        response = client.get_object(MINIO_BUCKET, object_name)
        pdf_data = response.read()
        
        # 返回PDF文件
        from fastapi.responses import Response
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={paper.original_name}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"View error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览失败: {str(e)}"
        )


@router.delete("/delete/{object_name}", response_model=DeleteResponse)
async def delete_paper(
    object_name: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除论文（同时删除 Milvus 向量）"""
    try:
        # 验证权限
        paper = db.query(Paper).filter(
            Paper.object_name == object_name,
            Paper.user_id == current_user["id"]
        ).first()
        
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="论文不存在或无权访问"
            )
        
        # 1. 从 Milvus 删除向量索引
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                vector_response = await client.delete(
                    f"{VECTOR_SEARCH_SERVICE_URL}/api/vector/delete/{object_name}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if vector_response.status_code == 200:
                    logger.info(f"✓ Milvus vectors deleted for: {object_name}")
                else:
                    logger.warning(f"Failed to delete Milvus vectors: {vector_response.status_code}")
        except Exception as e:
            logger.warning(f"Error deleting Milvus vectors: {e}")
            # 继续删除 MinIO 和数据库记录
        
        # 2. 从 MinIO 删除文件
        minio_client = get_minio_client()
        minio_client.remove_object(MINIO_BUCKET, object_name)
        
        # 3. 从数据库删除记录
        db.delete(paper)
        db.commit()
        
        logger.info(f"Paper deleted: {object_name} by user {current_user['id']}")
        
        return DeleteResponse(
            success=True,
            message="删除成功（包括向量索引）",
            object_name=object_name
        )
        
    except S3Error as e:
        logger.error(f"MinIO delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MinIO删除失败"
        )
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "paper-storage"}

