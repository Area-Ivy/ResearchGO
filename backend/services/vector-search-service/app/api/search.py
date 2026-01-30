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
from app.services.hybrid_search_service import get_hybrid_search_service
from app.services.bm25_service import get_bm25_service
from app.utils.auth_client import get_current_user
from app.utils.text_chunker import split_text_into_chunks
from datetime import datetime
from typing import Optional

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
    
    支持两种模式：
    1. 简单模式：只传 content，自动切分
    2. 结构化模式：传 structured_chunks（来自 LLM 结构解析 + 递归语义切分）
       - source 字段存储 section_type (abstract, introduction, methods, etc.)
       - page_range 字段存储 hierarchy_path (如 "Methods > Data Collection")
    """
    try:
        use_structured = bool(request.structured_chunks)
        section_type_counts = {}
        
        if use_structured and request.structured_chunks:
            # 结构化模式：使用 LLM 解析 + 递归语义切分的结果
            logger.info(f"Indexing with structured chunks: {len(request.structured_chunks)} chunks")
            
            chunks = []
            for sc in request.structured_chunks:
                chunks.append({
                    'text': sc.content,
                    'total_chars': sc.char_count if sc.char_count > 0 else len(sc.content),
                    'section_type': sc.section_type,
                    'section_title': sc.section_title,
                    'hierarchy_path': sc.hierarchy_path,
                    'is_complete_section': sc.is_complete_section,
                    'metadata': sc.metadata
                })
                # 统计章节类型分布
                section_type_counts[sc.section_type] = section_type_counts.get(sc.section_type, 0) + 1
            
            logger.info(f"  - 章节类型分布: {section_type_counts}")
        else:
            # 简单模式：自动切分文本
            chunks = split_text_into_chunks(
                text=request.content,
                chunk_size=request.max_chunk_size,
                chunk_overlap=200,
                max_chunks=100
            )
            # 为简单模式添加默认字段
            for chunk in chunks:
                chunk['section_type'] = 'other'
                chunk['section_title'] = ''
                chunk['hierarchy_path'] = 'Full Text'
                chunk['is_complete_section'] = False
                chunk['metadata'] = {}
        
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
        
        # 结构化模式：page_range 存储 hierarchy_path (最大200字符)
        page_ranges = [chunk.get('hierarchy_path', 'unknown')[:200] for chunk in chunks]
        
        upload_times = [upload_time] * len(chunks)
        
        # 结构化模式：source 存储 section_type
        sources = [chunk.get('section_type', 'other') for chunk in chunks]
        
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
        
        # 5. 同步 BM25 索引（用于混合检索）
        try:
            bm25_chunks = []
            for i, text in enumerate(contents):
                bm25_chunks.append({
                    'content': text,
                    'chunk_id': chunk_ids[i],
                    'chunk_index': chunk_indices[i],
                    'title': titles[i],
                    'file_name': file_names[i],
                    'section_type': sources[i],  # 添加章节类型
                    'hierarchy_path': page_ranges[i]  # 添加层级路径
                })
            
            bm25_service = get_bm25_service()
            bm25_service.add_documents(request.paper_id, bm25_chunks)
            bm25_service.rebuild_global_index()
            logger.info(f"✓ BM25 index synced for: {request.paper_id}")
        except Exception as e:
            logger.warning(f"BM25 index sync failed (non-critical): {e}")
        
        return IndexPaperResponse(
            paper_id=request.paper_id,
            chunks_created=len(chunks),
            message=f"成功创建 {len(chunks)} 个结构化chunks的向量索引" if use_structured else f"成功创建 {len(chunks)} 个chunks的向量索引",
            section_types=section_type_counts if use_structured else None,
            structured=use_structured
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
    删除论文的向量索引（同时删除 BM25 索引）
    """
    try:
        # 1. 删除 Milvus 向量索引
        milvus_service = get_milvus_service()
        success = milvus_service.delete_by_paper_id([paper_id])
        
        if not success:
            raise HTTPException(status_code=500, detail="删除向量索引失败")
        
        # 2. 删除 BM25 索引
        try:
            bm25_service = get_bm25_service()
            bm25_service.remove_documents(paper_id)
            logger.info(f"✓ BM25 index removed for: {paper_id}")
        except Exception as e:
            logger.warning(f"BM25 index removal failed (non-critical): {e}")
        
        return {
            "success": True,
            "message": f"成功删除论文 {paper_id} 的向量索引和 BM25 索引"
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
    
    使用混合检索: Dense + BM25 + RRF + Reranker + 查询翻译
    """
    async def generate():
        start_time = time.time()
        
        try:
            logger.info(f"Paper QA Stream (Hybrid): paper_id='{request.paper_id}', question='{request.question[:50]}...'")
            
            # 获取服务
            hybrid_service = get_hybrid_search_service()
            openai_service = get_openai_service()
            
            # 1. 混合检索 (Dense + BM25 + RRF + Reranker + 查询翻译)
            search_result = await hybrid_service.search(
                query=request.question,
                top_k=request.top_k,
                paper_id=request.paper_id,
                use_reranker=True,
                translate_query=True,
                initial_k=20  # 初始检索更多，让 RRF 和 Reranker 有更多候选
            )
            
            paper_chunks = search_result.get("final_results", [])
            
            # 日志：显示检索统计
            stats = search_result.get("stats", {})
            logger.info(f"  - Dense: {stats.get('dense_count', 0)}, Sparse: {stats.get('sparse_count', 0)}")
            logger.info(f"  - RRF Fused: {stats.get('fused_count', 0)}, Final: {stats.get('final_count', 0)}")
            if search_result.get("query_translated"):
                logger.info(f"  - Query translated: '{request.question}' -> '{search_result.get('translated_query')}'")
            
            if not paper_chunks:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "content": "抱歉，在当前论文中没有找到与您问题相关的内容。",
                        "done": True
                    })
                }
                return
            
            # 2. 构建上下文
            context_parts = []
            for i, chunk in enumerate(paper_chunks[:request.top_k], 1):
                section_info = chunk.get('page_range', 'unknown')  # 实际存储的是 hierarchy_path
                context_parts.append(f"【片段 {i}】({section_info})\n{chunk.get('content', '')}\n")
            context = "\n".join(context_parts)
            
            # 3. 发送引用信息（混合检索结果格式）
            references = []
            for chunk in paper_chunks[:request.top_k]:
                references.append({
                    "id": chunk.get('id', 0),
                    "distance": chunk.get('distance', 0),
                    "relevance_score": chunk.get('rerank_score', chunk.get('rrf_score', chunk.get('relevance_score', 0))),
                    "paper_id": chunk.get('paper_id', ''),
                    "title": chunk.get('title', ''),
                    "file_name": chunk.get('file_name', ''),
                    "upload_time": chunk.get('upload_time', ''),
                    "chunk_id": chunk.get('chunk_id', ''),
                    "chunk_index": chunk.get('chunk_index', 0),
                    "content": chunk.get('content', ''),
                    "chunk_chars": chunk.get('chunk_chars', 0),
                    "page_range": chunk.get('page_range', ''),  # 存储 hierarchy_path
                    "source": chunk.get('source', '')  # 存储 section_type
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


@router.post("/hybrid-search")
async def hybrid_search(
    query: str,
    top_k: int = 10,
    paper_id: Optional[str] = None,
    use_reranker: bool = True,
    translate_query: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """
    混合检索 API（支持跨语言检索）
    
    检索流程:
    1. Query Translation (可选) → 翻译中文查询为英文
    2. Dense Search (Embedding + Milvus) → Top-20
    3. Sparse Search (BM25) → Top-20 (使用翻译后查询)
    4. RRF (Reciprocal Rank Fusion) → 融合结果
    5. Cross-Encoder Reranker (可选) → 重排序
    6. 返回 Top-K
    
    Args:
        query: 查询文本
        top_k: 返回数量
        paper_id: 限定论文ID（可选）
        use_reranker: 是否使用 Reranker
        translate_query: 是否启用查询翻译（跨语言检索）
    """
    start_time = time.time()
    
    try:
        hybrid_service = get_hybrid_search_service()
        
        result = await hybrid_service.search(
            query=query,
            top_k=top_k,
            paper_id=paper_id,
            use_reranker=use_reranker,
            translate_query=translate_query,
            initial_k=20
        )
        
        search_time = (time.time() - start_time) * 1000
        
        return {
            "query": query,
            "translated_query": result.get("translated_query"),
            "query_translated": result.get("query_translated", False),
            "results": result["final_results"],
            "total": result["stats"]["final_count"],
            "search_time_ms": round(search_time, 2),
            "stats": {
                "dense_count": result["stats"]["dense_count"],
                "sparse_count": result["stats"]["sparse_count"],
                "fused_count": result["stats"]["fused_count"],
                "final_count": result["stats"]["final_count"],
                "use_reranker": use_reranker,
                "translate_query": translate_query
            }
        }
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"混合检索失败: {str(e)}")


@router.post("/hybrid-qa")
async def hybrid_qa(
    request: PaperQARequest,
    use_reranker: bool = True,
    translate_query: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """
    混合检索问答 API（非流式，支持跨语言检索）
    
    使用 Hybrid Search + Reranker + Query Translation 获取更高质量的上下文
    """
    start_time = time.time()
    
    try:
        hybrid_service = get_hybrid_search_service()
        openai_service = get_openai_service()
        
        # 1. 混合检索（支持查询翻译）
        search_result = await hybrid_service.search(
            query=request.question,
            top_k=request.top_k,
            paper_id=request.paper_id,
            use_reranker=use_reranker,
            translate_query=translate_query
        )
        
        final_results = search_result["final_results"]
        
        # 2. 构建上下文
        references = []
        context_parts = []
        
        for i, hit in enumerate(final_results):
            references.append(SearchResult(
                id=hit.get('id', 0),
                distance=hit.get('distance', 0),
                relevance_score=hit.get('rerank_score', hit.get('rrf_score', 0)),
                paper_id=hit.get('paper_id', ''),
                title=hit.get('title', ''),
                file_name=hit.get('file_name', ''),
                upload_time=hit.get('upload_time', ''),
                chunk_id=hit.get('chunk_id', ''),
                chunk_index=hit.get('chunk_index', 0),
                content=hit.get('content', ''),
                chunk_chars=hit.get('chunk_chars', 0),
                page_range=hit.get('page_range', ''),
                source=hit.get('source', '')
            ))
            context_parts.append(f"[片段 {i+1}]\n{hit.get('content', '')}")
        
        context = "\n\n".join(context_parts)
        
        # 3. 生成答案
        if not context:
            answer = "抱歉，没有找到与您问题相关的内容。"
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
        logger.error(f"Hybrid QA failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


@router.post("/admin/recreate-collection")
async def recreate_collection(
    current_user: dict = Depends(get_current_user)
):
    """
    重建 Milvus Collection（会删除所有数据！）
    
    用于：
    - 更新 Schema（如字段长度限制）
    - 清空所有向量数据
    
    ⚠️ 警告：此操作不可逆，将删除所有已索引的论文向量！
    """
    try:
        milvus_service = get_milvus_service()
        
        # 断开连接
        milvus_service.disconnect()
        
        # 重新连接
        milvus_service.connect()
        
        # 强制重建
        success = milvus_service.create_collection(dim=1536, force_recreate=True)
        
        if success:
            milvus_service.create_index()
            
            # 清空 BM25 索引
            bm25_service = get_bm25_service()
            bm25_service.clear_all()
            
            return {
                "success": True,
                "message": "Collection 已重建，所有数据已清空。请重新上传论文。"
            }
        else:
            raise HTTPException(status_code=500, detail="重建 Collection 失败")
            
    except Exception as e:
        logger.error(f"Recreate collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重建失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "vector-search-service",
        "milvus_connected": True,
        "features": ["dense_search", "sparse_search", "hybrid_search", "reranker", "query_translation", "structured_indexing"]
    }

