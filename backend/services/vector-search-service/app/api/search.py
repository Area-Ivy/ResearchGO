"""
向量搜索API - 语义搜索和论文问答
"""
import time
import json
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse
import logging

from app.schemas.search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SearchResult,
    PaperQARequest,
    PaperQAResponse,
    IndexPaperRequest,
    IndexPaperResponse
)
from app.services.milvus_service import get_milvus_service
from app.services.openai_service import get_openai_service
from app.utils.auth_client import get_current_user
from app.utils.text_chunker import split_text_into_chunks
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vector", tags=["vector-search"])


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    语义搜索 - 在所有论文中搜索相关内容
    """
    start_time = time.time()
    
    try:
        # 1. 生成查询向量
        openai_service = get_openai_service()
        query_embeddings = await openai_service.generate_embeddings([request.query])
        
        # 2. 在Milvus中搜索
        milvus_service = get_milvus_service()
        
        # 构建过滤表达式（如果需要）
        filter_expr = None
        if request.uploaded_after:
            filter_expr = f'upload_time >= "{request.uploaded_after}"'
        
        results = milvus_service.search_similar(
            query_vectors=query_embeddings,
            top_k=request.top_k,
            filter_expr=filter_expr
        )
        
        # 3. 格式化结果
        search_results = []
        if results and len(results) > 0:
            for hit in results[0]:
                search_results.append(SearchResult(**hit))
        
        search_time = (time.time() - start_time) * 1000
        
        return SemanticSearchResponse(
            query=request.query,
            results=search_results,
            total=len(search_results),
            search_time_ms=round(search_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.post("/qa", response_model=PaperQAResponse)
async def paper_qa(
    request: PaperQARequest,
    current_user: dict = Depends(get_current_user)
):
    """
    论文问答 - 基于特定论文回答问题
    """
    start_time = time.time()
    
    try:
        # 1. 生成问题向量
        openai_service = get_openai_service()
        question_embeddings = await openai_service.generate_embeddings([request.question])
        
        # 2. 在Milvus中搜索相关chunk（限定在指定论文内）
        milvus_service = get_milvus_service()
        filter_expr = f'paper_id == "{request.paper_id}"'
        
        results = milvus_service.search_similar(
            query_vectors=question_embeddings,
            top_k=request.top_k,
            filter_expr=filter_expr
        )
        
        # 3. 提取相关内容作为上下文
        references = []
        context_parts = []
        
        if results and len(results) > 0:
            for hit in results[0]:
                references.append(SearchResult(**hit))
                context_parts.append(f"[片段 {len(context_parts)+1}]\n{hit['content']}")
        
        context = "\n\n".join(context_parts)
        
        # 4. 使用OpenAI生成答案
        if not context:
            answer = "抱歉，在该论文中没有找到与您问题相关的内容。"
        else:
            answer = await openai_service.generate_answer(
                question=request.question,
                context=context,
                chat_history=request.chat_history
            )
        
        response_time = (time.time() - start_time) * 1000
        
        return PaperQAResponse(
            question=request.question,
            answer=answer,
            references=references,
            response_time_ms=round(response_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Paper QA failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


@router.post("/index", response_model=IndexPaperResponse)
async def index_paper(
    request: IndexPaperRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    索引论文 - 将论文内容切分并生成向量索引
    """
    try:
        # 1. 切分文本
        chunks = split_text_into_chunks(
            text=request.content,
            chunk_size=request.max_chunk_size,
            chunk_overlap=200,
            max_chunks=100
        )
        
        if not chunks:
            raise HTTPException(status_code=400, detail="无法切分文本")
        
        # 2. 生成向量嵌入
        openai_service = get_openai_service()
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = await openai_service.generate_embeddings(chunk_texts)
        
        # 3. 准备数据
        upload_time = datetime.now().isoformat()
        paper_ids = [request.paper_id] * len(chunks)
        chunk_ids = [f"{request.paper_id}#{i}" for i in range(len(chunks))]
        chunk_indices = list(range(len(chunks)))
        titles = [request.title] * len(chunks)
        file_names = [request.file_name] * len(chunks)
        contents = chunk_texts
        chunk_chars = [chunk['total_chars'] for chunk in chunks]
        page_ranges = ["unknown"] * len(chunks)  # 需要从PDF提取时计算
        upload_times = [upload_time] * len(chunks)
        sources = ["chunk"] * len(chunks)
        
        # 4. 插入Milvus
        milvus_service = get_milvus_service()
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
        
        if not success:
            raise HTTPException(status_code=500, detail="索引插入失败")
        
        return IndexPaperResponse(
            paper_id=request.paper_id,
            chunks_created=len(chunks),
            message=f"成功创建 {len(chunks)} 个chunks的向量索引"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Index paper failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"索引失败: {str(e)}")


@router.delete("/delete/{paper_id}")
async def delete_paper_vectors(
    paper_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除论文的向量索引
    """
    try:
        milvus_service = get_milvus_service()
        success = milvus_service.delete_by_paper_id([paper_id])
        
        if not success:
            raise HTTPException(status_code=500, detail="删除向量索引失败")
        
        return {
            "success": True,
            "message": f"成功删除论文 {paper_id} 的向量索引"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete vectors failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """
    获取向量数据库统计信息
    """
    try:
        milvus_service = get_milvus_service()
        stats = milvus_service.get_collection_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Get stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/qa-stream")
async def paper_qa_stream(
    request: PaperQARequest,
    current_user: dict = Depends(get_current_user)
):
    """
    论文问答 - 流式输出（SSE）
    """
    async def generate():
        start_time = time.time()
        
        try:
            logger.info(f"Paper QA Stream: paper_id='{request.paper_id}', question='{request.question[:50]}...'")
            
            # 获取服务
            milvus_service = get_milvus_service()
            openai_service = get_openai_service()
            
            # 1. 生成问题向量
            question_embeddings = await openai_service.generate_embeddings([request.question])
            
            # 2. 检索相关内容
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
                        "content": "抱歉，在当前论文中没有找到与您问题相关的内容。",
                        "done": True
                    })
                }
                return
            
            # 3. 构建上下文
            paper_chunks = results[0]
            context_parts = []
            for i, chunk in enumerate(paper_chunks[:request.top_k], 1):
                context_parts.append(f"【片段 {i}】(页码: {chunk['page_range']})\n{chunk['content']}\n")
            context = "\n".join(context_parts)
            
            # 4. 发送引用信息
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
            
            # 5. 构建提示词
            system_prompt = """你是一个专业的学术助手，帮助用户理解和分析研究论文。

基于提供的论文内容片段，请准确、详细地回答用户的问题。

注意事项：
1. 只基于提供的上下文回答，不要编造信息
2. 如果上下文中没有相关信息，明确告知用户
3. 回答要专业、准确、有条理
4. 必要时可以引用原文
5. 使用中文回答"""

            user_prompt = f"""参考内容：
{context}

问题：{request.question}

请基于以上参考内容回答问题。"""

            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加聊天历史
            if request.chat_history:
                for msg in request.chat_history[-5:]:
                    messages.append(msg)
            
            messages.append({"role": "user", "content": user_prompt})
            
            # 6. 流式生成答案
            full_response = ""
            async for chunk_text in openai_service.chat_completion_stream(messages):
                full_response += chunk_text
                yield {
                    "event": "message",
                    "data": json.dumps({"content": chunk_text})
                }
            
            # 7. 发送完成信号
            response_time = (time.time() - start_time) * 1000
            yield {
                "event": "done",
                "data": json.dumps({
                    "done": True,
                    "response_time_ms": round(response_time, 2)
                })
            }
            
        except Exception as e:
            logger.error(f"Paper QA stream failed: {str(e)}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(generate())


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "vector-search-service",
        "milvus_connected": True
    }

