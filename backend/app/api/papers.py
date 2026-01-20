"""
Papers API
文献管理相关的 API 端点
"""
import io
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import pdfplumber
from app.models.papers import (
    PaperUploadResponse,
    PaperInfo,
    PaperListResponse,
    DeleteResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SearchResult,
    PaperQARequest,
    PaperQAResponse
)
from app.services.minio_service import MinIOService
from app.services.milvus_service import MilvusService
from app.services.openai_service import OpenAIService
from app.utils.text_chunker import split_text_into_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/papers", tags=["papers"])

# 服务实例（延迟初始化）
_minio_service = None
_milvus_service = None
_openai_service = None


def get_minio_service():
    """获取或创建 MinIO 服务实例"""
    global _minio_service
    if _minio_service is None:
        _minio_service = MinIOService()
    return _minio_service


def get_milvus_service():
    """获取或创建 Milvus 服务实例"""
    global _milvus_service
    if _milvus_service is None:
        _milvus_service = MilvusService()
        # 连接并确保集合存在
        if _milvus_service.connect():
            _milvus_service.create_collection(dim=1536)  # text-embedding-3-small 的维度是 1536
            _milvus_service.create_index()
            logger.info("Milvus service initialized successfully")
    return _milvus_service


def get_openai_service():
    """获取或创建 OpenAI 服务实例"""
    global _openai_service
    if _openai_service is None:
        try:
            _openai_service = OpenAIService()
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.warning(f"OpenAI service not available: {e}")
            _openai_service = None
    return _openai_service


async def extract_text_from_pdf(pdf_data: bytes, max_pages: int = None) -> str:
    """
    从 PDF 中提取文本内容
    
    Args:
        pdf_data: PDF 文件字节数据
        max_pages: 最大页数（None表示提取所有页）
        
    Returns:
        str: 提取的文本内容
    """
    try:
        text_content = []
        pdf_stream = io.BytesIO(pdf_data)
        
        with pdfplumber.open(pdf_stream) as pdf:
            total_pages = len(pdf.pages)
            pages_to_extract = min(total_pages, max_pages) if max_pages else total_pages
            
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


async def store_paper_in_milvus(
    paper_id: str,
    file_name: str,
    pdf_data: bytes,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    max_pages: int = 50
):
    """
    将论文切分成chunks并存储到 Milvus 向量数据库
    
    Args:
        paper_id: 论文ID（MinIO对象名）
        file_name: 原始文件名
        pdf_data: PDF文件数据
        chunk_size: chunk大小（字符数）
        chunk_overlap: chunk重叠大小
        max_pages: 最大提取页数
    """
    try:
        # 获取服务实例
        milvus_service = get_milvus_service()
        openai_service = get_openai_service()
        
        if not milvus_service or not openai_service:
            logger.warning("Milvus or OpenAI service not available, skipping vector storage")
            return
        
        # 1. 提取 PDF 文本
        logger.info(f"Extracting text from PDF: {file_name}")
        text = await extract_text_from_pdf(pdf_data, max_pages=max_pages)
        
        if not text or len(text) < 100:
            logger.warning(f"No sufficient text extracted from PDF: {file_name}")
            return
        
        # 2. 切分文本成chunks
        logger.info(f"Splitting text into chunks (size: {chunk_size}, overlap: {chunk_overlap})")
        chunks = split_text_into_chunks(
            text=text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            max_chunks=100,
            method="sliding_window"
        )
        
        if not chunks:
            logger.warning(f"No chunks generated for: {file_name}")
            return
        
        logger.info(f"Generated {len(chunks)} chunks for {file_name}")
        
        # 3. 生成标题（从文件名提取）
        title = file_name.replace('.pdf', '').replace('_', ' ')
        
        # 4. 批量生成嵌入向量
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = await openai_service.generate_embeddings(chunk_texts)
        
        if not embeddings or len(embeddings) != len(chunks):
            logger.warning(f"Failed to generate embeddings for: {file_name}")
            return
        
        # 5. 准备数据和metadata
        from datetime import datetime
        
        upload_time = datetime.utcnow().isoformat() + 'Z'
        
        paper_ids = [paper_id] * len(chunks)
        chunk_ids = [f"{paper_id}#chunk_{chunk['chunk_index']}" for chunk in chunks]
        chunk_indices = [chunk['chunk_index'] for chunk in chunks]
        titles = [title] * len(chunks)
        file_names = [file_name] * len(chunks)
        contents = [chunk['text'] for chunk in chunks]
        chunk_chars = [chunk['total_chars'] for chunk in chunks]
        
        # 估算页码范围（基于chunk索引，假设每页约2个chunks）
        page_ranges = []
        for chunk in chunks:
            start_page = (chunk['chunk_index'] * chunk_size) // 2000 + 1  # 粗略估算
            end_page = min(start_page + 2, max_pages)
            page_ranges.append(f"{start_page}-{end_page}")
        
        upload_times = [upload_time] * len(chunks)
        sources = ["chunk"] * len(chunks)
        
        # 6. 存储到 Milvus（包含metadata）
        logger.info(f"Storing {len(chunks)} chunks with metadata in Milvus for: {file_name}")
        success = milvus_service.insert_vectors(
            paper_ids=paper_ids,
            chunk_ids=chunk_ids,
            chunk_indices=chunk_indices,
            embeddings=embeddings,
            titles=titles,
            file_names=file_names,
            contents=contents,
            chunk_chars=chunk_chars,
            page_ranges=page_ranges,
            upload_times=upload_times,
            sources=sources
        )
        
        if success:
            logger.info(f"Successfully stored {len(chunks)} chunks in Milvus: {file_name}")
        else:
            logger.warning(f"Failed to store chunks in Milvus: {file_name}")
            
    except Exception as e:
        # 不抛出异常，只记录错误，避免影响上传流程
        logger.error(f"Error storing paper in Milvus: {e}", exc_info=True)


@router.post("/upload", response_model=PaperUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_paper(file: UploadFile = File(...)):
    """
    上传论文文件
    
    - 支持 PDF 文件
    - 文件会被存储到 MinIO 和 Milvus
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
        
        # 读取文件数据（用于 MinIO 和 Milvus）
        file_data = await file.read()
        
        # 1. 上传到 MinIO
        service = get_minio_service()
        file_stream = io.BytesIO(file_data)
        result = await service.upload_file(
            file_data=file_stream,
            file_name=file.filename,
            content_type=file.content_type or "application/pdf"
        )
        
        # 2. 异步存储到 Milvus（不阻塞响应）
        try:
            await store_paper_in_milvus(
                paper_id=result["object_name"],
                file_name=file.filename,
                pdf_data=file_data
            )
        except Exception as milvus_error:
            # Milvus 存储失败不影响上传结果
            logger.error(f"Failed to store in Milvus: {milvus_error}")
        
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
    - 同时从 Milvus 中删除对应的向量数据
    """
    try:
        logger.info(f"Deleting paper: {object_name}")
        
        # 1. 从 MinIO 删除
        service = get_minio_service()
        success = await service.delete_file(object_name)
        
        # 2. 从 Milvus 删除
        try:
            milvus_service = get_milvus_service()
            if milvus_service:
                logger.info(f"Deleting paper from Milvus: {object_name}")
                milvus_service.delete_by_paper_id([object_name])
        except Exception as milvus_error:
            # Milvus 删除失败不影响结果
            logger.error(f"Failed to delete from Milvus: {milvus_error}")
        
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


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """
    语义搜索论文
    
    - 使用向量相似度检索相关论文片段
    - 支持按上传时间过滤
    - 返回包含完整metadata的结果
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Semantic search: query='{request.query}', top_k={request.top_k}")
        
        # 获取服务实例
        milvus_service = get_milvus_service()
        openai_service = get_openai_service()
        
        if not milvus_service or not openai_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service not available (Milvus or OpenAI not initialized)"
            )
        
        # 1. 生成查询向量
        logger.info(f"Generating query embedding for: {request.query[:50]}...")
        query_embeddings = await openai_service.generate_embeddings([request.query])
        
        if not query_embeddings:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate query embedding"
            )
        
        # 2. 向量检索
        logger.info(f"Searching in Milvus with top_k={request.top_k}")
        results = milvus_service.search_similar(
            query_vectors=query_embeddings,
            top_k=request.top_k
        )
        
        if not results or not results[0]:
            logger.info("No results found")
            return SemanticSearchResponse(
                query=request.query,
                results=[],
                total=0,
                search_time_ms=round((time.time() - start_time) * 1000, 2)
            )
        
        # 3. 格式化结果
        chunks = results[0]
        
        # 4. 时间过滤（如果指定）
        if request.uploaded_after:
            chunks = [
                c for c in chunks 
                if c.get('upload_time', '') >= request.uploaded_after
            ]
            logger.info(f"Filtered by upload_time, remaining: {len(chunks)}")
        
        # 5. 转换为响应模型
        search_results = []
        for chunk in chunks:
            search_results.append(SearchResult(
                id=chunk['id'],
                distance=chunk['distance'],
                relevance_score=chunk['relevance_score'],
                paper_id=chunk['paper_id'],
                title=chunk['title'],
                file_name=chunk['file_name'],
                upload_time=chunk['upload_time'],
                chunk_id=chunk['chunk_id'],
                chunk_index=chunk['chunk_index'],
                content=chunk['content'],
                chunk_chars=chunk['chunk_chars'],
                page_range=chunk['page_range'],
                source=chunk['source']
            ))
        
        search_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Search completed in {search_time_ms}ms, found {len(search_results)} results")
        
        return SemanticSearchResponse(
            query=request.query,
            results=search_results,
            total=len(search_results),
            search_time_ms=search_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in semantic search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/qa", response_model=PaperQAResponse)
async def paper_qa(request: PaperQARequest):
    """
    论文问答 - RAG (Retrieval Augmented Generation)
    
    - 基于向量检索找到相关内容
    - 使用 LLM 生成回答
    - 返回答案和参考内容
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Paper QA: paper_id='{request.paper_id}', question='{request.question[:50]}...'")
        
        # 获取服务实例
        milvus_service = get_milvus_service()
        openai_service = get_openai_service()
        
        if not milvus_service or not openai_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="QA service not available (Milvus or OpenAI not initialized)"
            )
        
        # 1. 生成问题的向量
        logger.info("Generating question embedding...")
        question_embeddings = await openai_service.generate_embeddings([request.question])
        
        if not question_embeddings:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate question embedding"
            )
        
        # 2. 在 Milvus 中检索相关内容（仅检索指定论文）
        logger.info(f"Searching relevant content in paper '{request.paper_id}' with top_k={request.top_k}")
        
        # 构建过滤表达式，只检索指定论文的内容
        filter_expr = f'paper_id == "{request.paper_id}"'
        
        results = milvus_service.search_similar(
            query_vectors=question_embeddings,
            top_k=request.top_k,
            filter_expr=filter_expr
        )
        
        if not results or not results[0]:
            logger.info("No relevant content found in the paper")
            answer = "抱歉，在当前论文中没有找到与您问题相关的内容。请尝试换个问题。"
            return PaperQAResponse(
                question=request.question,
                answer=answer,
                references=[],
                response_time_ms=round((time.time() - start_time) * 1000, 2)
            )
        
        # 3. 获取检索结果（已经过滤为指定论文）
        paper_chunks = results[0]
        logger.info(f"Found {len(paper_chunks)} relevant chunks in the paper")
        
        # 获取论文标题和文件名（从第一个chunk中获取）
        paper_title = paper_chunks[0].get('title', '未知标题') if paper_chunks else '未知标题'
        paper_filename = paper_chunks[0].get('file_name', '未知文件') if paper_chunks else '未知文件'
        
        # 4. 构建上下文
        context_parts = []
        for i, chunk in enumerate(paper_chunks[:request.top_k], 1):
            context_parts.append(
                f"【片段 {i}】(页码: {chunk['page_range']})\n{chunk['content']}\n"
            )
        context = "\n".join(context_parts)
        
        # 5. 构建 prompt
        system_prompt = """你是一个专业的学术论文分析助手。你的任务是基于提供的论文内容回答用户的问题。

请遵循以下原则：
1. 基于提供的论文内容回答问题，可以进行合理的总结和推断
2. 当用户问"这篇论文"时，指的就是当前讨论的论文，你应该基于提供的内容片段来回答
3. 对于宽泛的问题（如"主要研究内容是什么"），请从提供的内容片段中提取关键信息，进行综合总结
4. 论文标题本身往往就反映了研究主题，可以结合标题和内容片段来回答
5. 回答要准确、专业、清晰，使用中文
6. 如果问题涉及多个方面，请分点回答
7. 即使内容片段不完整，也要尽力基于现有信息给出有价值的回答，而不是简单地说"无法确定"
8. 不要在回答中显示引用标记（如 [引用 1]），直接整合内容自然地回答即可
"""

        user_prompt = f"""当前正在分析的论文：
【论文标题】{paper_title}
【文件名】{paper_filename}

【论文相关内容片段】
{context}

【用户问题】
{request.question}

【回答要求】
请基于上述论文标题和内容片段，回答用户的问题。
- 如果用户问"这篇论文"，指的就是《{paper_title}》这篇论文
- 对于宽泛的问题，请综合论文标题和提供的内容片段进行总结性回答
- 论文标题通常包含了研究的核心主题，请善用这一信息
- 尽量给出有价值的回答，避免简单地说"无法确定"或"信息不足"
- 直接整合内容自然地回答，不要显示引用标记
"""

        # 6. 准备消息历史
        from app.models.chat import ChatMessage
        messages = [ChatMessage(role="system", content=system_prompt)]
        
        # 添加历史对话（最多保留最近5轮）
        for history_item in request.chat_history[-5:]:
            if history_item.get("role") and history_item.get("content"):
                messages.append(ChatMessage(
                    role=history_item["role"],
                    content=history_item["content"]
                ))
        
        # 添加当前问题
        messages.append(ChatMessage(role="user", content=user_prompt))
        
        # 7. 调用 LLM 生成回答
        logger.info("Generating answer with LLM...")
        answer = await openai_service.chat_completion(
            messages=messages,
            temperature=0.5,  # 适中的温度，既保证准确性又能进行合理推断
            max_tokens=2000
        )
        
        # 8. 转换为响应模型
        references = []
        for chunk in paper_chunks[:request.top_k]:
            references.append(SearchResult(
                id=chunk['id'],
                distance=chunk['distance'],
                relevance_score=chunk['relevance_score'],
                paper_id=chunk['paper_id'],
                title=chunk['title'],
                file_name=chunk['file_name'],
                upload_time=chunk['upload_time'],
                chunk_id=chunk['chunk_id'],
                chunk_index=chunk['chunk_index'],
                content=chunk['content'],
                chunk_chars=chunk['chunk_chars'],
                page_range=chunk['page_range'],
                source=chunk['source']
            ))
        
        response_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"QA completed in {response_time_ms}ms")
        
        return PaperQAResponse(
            question=request.question,
            answer=answer,
            references=references,
            response_time_ms=response_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in paper QA: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QA failed: {str(e)}"
        )


@router.post("/qa-stream")
async def paper_qa_stream(request: PaperQARequest):
    """
    论文问答 - 流式输出
    
    - 基于向量检索找到相关内容
    - 使用 LLM 流式生成回答
    - 返回 SSE 流
    """
    import time
    import json
    
    async def generate():
        start_time = time.time()
        
        try:
            logger.info(f"Paper QA Stream: paper_id='{request.paper_id}', question='{request.question[:50]}...'")
            
            # 获取服务实例
            milvus_service = get_milvus_service()
            openai_service = get_openai_service()
            
            if not milvus_service or not openai_service:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "QA service not available"})
                }
                return
            
            # 1. 生成问题的向量
            logger.info("Generating question embedding...")
            question_embeddings = await openai_service.generate_embeddings([request.question])
            
            if not question_embeddings:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Failed to generate question embedding"})
                }
                return
            
            # 2. 在 Milvus 中检索相关内容
            logger.info(f"Searching relevant content in paper '{request.paper_id}' with top_k={request.top_k}")
            filter_expr = f'paper_id == "{request.paper_id}"'
            
            results = milvus_service.search_similar(
                query_vectors=question_embeddings,
                top_k=request.top_k,
                filter_expr=filter_expr
            )
            
            if not results or not results[0]:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "content": "抱歉，在当前论文中没有找到与您问题相关的内容。请尝试换个问题。",
                        "done": True
                    })
                }
                return
            
            # 3. 获取检索结果
            paper_chunks = results[0]
            logger.info(f"Found {len(paper_chunks)} relevant chunks in the paper")
            
            # 获取论文标题和文件名
            paper_title = paper_chunks[0].get('title', '未知标题') if paper_chunks else '未知标题'
            paper_filename = paper_chunks[0].get('file_name', '未知文件') if paper_chunks else '未知文件'
            
            # 4. 构建上下文
            context_parts = []
            for i, chunk in enumerate(paper_chunks[:request.top_k], 1):
                context_parts.append(
                    f"【片段 {i}】(页码: {chunk['page_range']})\n{chunk['content']}\n"
                )
            context = "\n".join(context_parts)
            
            # 发送引用信息
            references = []
            for chunk in paper_chunks[:request.top_k]:
                references.append({
                    "id": chunk['id'],
                    "distance": chunk['distance'],
                    "relevance_score": chunk['relevance_score'],
                    "paper_id": chunk['paper_id'],
                    "title": chunk['title'],
                    "file_name": chunk['file_name'],
                    "upload_time": chunk['upload_time'],
                    "chunk_id": chunk['chunk_id'],
                    "chunk_index": chunk['chunk_index'],
                    "content": chunk['content'],
                    "chunk_chars": chunk['chunk_chars'],
                    "page_range": chunk['page_range'],
                    "source": chunk['source']
                })
            
            yield {
                "event": "references",
                "data": json.dumps({"references": references})
            }
            
            # 5. 构建 prompt
            system_prompt = """你是一个专业的学术论文分析助手。你的任务是基于提供的论文内容回答用户的问题。

请遵循以下原则：
1. 基于提供的论文内容回答问题，可以进行合理的总结和推断
2. 当用户问"这篇论文"时，指的就是当前讨论的论文，你应该基于提供的内容片段来回答
3. 对于宽泛的问题（如"主要研究内容是什么"），请从提供的内容片段中提取关键信息，进行综合总结
4. 论文标题本身往往就反映了研究主题，可以结合标题和内容片段来回答
5. 回答要准确、专业、清晰，使用中文
6. 如果问题涉及多个方面，请分点回答
7. 即使内容片段不完整，也要尽力基于现有信息给出有价值的回答，而不是简单地说"无法确定"
8. 可以使用 Markdown 格式来组织回答，包括标题、列表、粗体等
9. 不要在回答中显示引用标记（如 [引用 1]），直接整合内容自然地回答即可
"""

            user_prompt = f"""当前正在分析的论文：
【论文标题】{paper_title}
【文件名】{paper_filename}

【论文相关内容片段】
{context}

【用户问题】
{request.question}

【回答要求】
请基于上述论文标题和内容片段，回答用户的问题。
- 如果用户问"这篇论文"，指的就是《{paper_title}》这篇论文
- 对于宽泛的问题，请综合论文标题和提供的内容片段进行总结性回答
- 论文标题通常包含了研究的核心主题，请善用这一信息
- 尽量给出有价值的回答，避免简单地说"无法确定"或"信息不足"
- 使用 Markdown 格式组织回答，使其更易读
- 直接整合内容自然地回答，不要显示引用标记
"""

            # 6. 准备消息历史
            from app.models.chat import ChatMessage
            messages = [ChatMessage(role="system", content=system_prompt)]
            
            # 添加历史对话（最多保留最近5轮）
            for history_item in request.chat_history[-5:]:
                if history_item.get("role") and history_item.get("content"):
                    messages.append(ChatMessage(
                        role=history_item["role"],
                        content=history_item["content"]
                    ))
            
            # 添加当前问题
            messages.append(ChatMessage(role="user", content=user_prompt))
            
            # 7. 流式调用 LLM 生成回答
            logger.info("Generating answer with LLM (streaming)...")
            
            async for chunk in openai_service.chat_completion_stream(
                messages=messages,
                temperature=0.5,
                max_tokens=2000
            ):
                yield {
                    "event": "message",
                    "data": json.dumps({"content": chunk})
                }
            
            # 发送完成信号
            response_time_ms = round((time.time() - start_time) * 1000, 2)
            yield {
                "event": "done",
                "data": json.dumps({
                    "response_time_ms": response_time_ms
                })
            }
            
            logger.info(f"QA stream completed in {response_time_ms}ms")
            
        except Exception as e:
            logger.error(f"Error in paper QA stream: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(generate())


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

