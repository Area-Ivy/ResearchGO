"""
混合检索服务
实现 Dense (Embedding) + Sparse (BM25) 检索融合
使用 RRF (Reciprocal Rank Fusion) 算法
"""
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.services.milvus_service import get_milvus_service
from app.services.bm25_service import get_bm25_service
from app.services.reranker_service import get_reranker_service
from app.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

# RRF 常数 k（通常设为 60）
RRF_K = 60


class HybridSearchService:
    """混合检索服务"""
    
    def __init__(self):
        self.milvus_service = None
        self.bm25_service = None
        self.reranker_service = None
        self.openai_service = None
    
    def _get_services(self):
        """延迟获取服务实例"""
        if self.milvus_service is None:
            self.milvus_service = get_milvus_service()
        if self.bm25_service is None:
            self.bm25_service = get_bm25_service()
        if self.reranker_service is None:
            self.reranker_service = get_reranker_service()
        if self.openai_service is None:
            self.openai_service = get_openai_service()
    
    def reciprocal_rank_fusion(
        self,
        result_lists: List[List[Dict[str, Any]]],
        k: int = RRF_K,
        id_field: str = "chunk_id"
    ) -> List[Dict[str, Any]]:
        """
        RRF (Reciprocal Rank Fusion) 算法
        
        公式: RRF(d) = Σ 1 / (k + rank_i(d))
        
        Args:
            result_lists: 多个检索结果列表
            k: RRF 常数（默认 60）
            id_field: 用于标识文档的字段
            
        Returns:
            融合后的结果列表
        """
        rrf_scores = defaultdict(float)
        doc_data = {}  # 保存文档数据
        
        for results in result_lists:
            for rank, doc in enumerate(results):
                doc_id = doc.get(id_field)
                if doc_id:
                    # RRF 公式
                    rrf_scores[doc_id] += 1.0 / (k + rank + 1)  # rank 从 0 开始
                    
                    # 保存文档数据（如果还没有）
                    if doc_id not in doc_data:
                        doc_data[doc_id] = doc.copy()
        
        # 按 RRF 分数排序
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # 构建结果
        results = []
        for doc_id in sorted_ids:
            doc = doc_data[doc_id].copy()
            doc['rrf_score'] = rrf_scores[doc_id]
            results.append(doc)
        
        return results
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        paper_id: Optional[str] = None,
        use_reranker: bool = True,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
        initial_k: int = 20,
        translate_query: bool = True
    ) -> Dict[str, Any]:
        """
        混合检索
        
        流程:
        1. Query Translation (可选) → 翻译中文查询为英文
        2. Dense Search (Embedding + Milvus) → Top-initial_k
        3. Sparse Search (BM25) → Top-initial_k (使用翻译后查询)
        4. RRF Fusion → 融合结果
        5. Reranker (可选) → 重排序
        6. 返回 Top-top_k
        
        Args:
            query: 查询文本
            top_k: 最终返回数量
            paper_id: 限定论文ID（可选）
            use_reranker: 是否使用 Reranker
            dense_weight: 稠密检索权重
            sparse_weight: 稀疏检索权重
            initial_k: 初始检索数量
            translate_query: 是否启用查询翻译（跨语言检索）
            
        Returns:
            检索结果和统计信息
        """
        self._get_services()
        
        results = {
            "query": query,
            "translated_query": None,
            "query_translated": False,
            "dense_results": [],
            "sparse_results": [],
            "fused_results": [],
            "final_results": [],
            "stats": {
                "dense_count": 0,
                "sparse_count": 0,
                "fused_count": 0,
                "final_count": 0
            }
        }
        
        try:
            # 0. Query Translation (跨语言检索)
            search_query = query  # 统一的搜索查询
            
            if translate_query:
                source_lang = self.openai_service.detect_language(query)
                logger.info(f"Detected query language: {source_lang}")
                
                if source_lang in ['zh', 'mixed']:
                    # 翻译中文查询为英文，统一用于 Dense 和 Sparse 检索
                    translated, was_translated = await self.openai_service.translate_query(
                        query, target_language='en'
                    )
                    if was_translated:
                        search_query = translated
                        results["translated_query"] = translated
                        results["query_translated"] = True
                        logger.info(f"Query translated: '{query}' -> '{translated}'")
            
            # 1. Dense Search (Embedding) - 使用翻译后的查询
            logger.info(f"Performing dense search with query: '{search_query}'")
            query_embeddings = await self.openai_service.generate_embeddings([search_query])
            
            filter_expr = f'paper_id == "{paper_id}"' if paper_id else None
            
            dense_results_raw = self.milvus_service.search_similar(
                query_vectors=query_embeddings,
                top_k=initial_k,
                filter_expr=filter_expr
            )
            
            dense_results = dense_results_raw[0] if dense_results_raw else []
            results["dense_results"] = dense_results
            results["stats"]["dense_count"] = len(dense_results)
            logger.info(f"Dense search returned {len(dense_results)} results")
            
            # 2. Sparse Search (BM25) - 同样使用翻译后的查询
            logger.info(f"Performing sparse search with query: '{search_query}'")
            sparse_results = self.bm25_service.search(
                query=search_query,
                top_k=initial_k,
                paper_id=paper_id
            )
            results["sparse_results"] = sparse_results
            results["stats"]["sparse_count"] = len(sparse_results)
            logger.info(f"Sparse search returned {len(sparse_results)} results")
            
            # 3. RRF Fusion
            logger.info("Fusing results with RRF...")
            
            # 为 dense results 添加 chunk_id（如果没有）
            for doc in dense_results:
                if 'chunk_id' not in doc or not doc['chunk_id']:
                    doc['chunk_id'] = f"{doc.get('paper_id', '')}#{doc.get('chunk_index', 0)}"
            
            for doc in sparse_results:
                if 'chunk_id' not in doc or not doc['chunk_id']:
                    doc['chunk_id'] = f"{doc.get('paper_id', '')}#{doc.get('chunk_index', 0)}"
            
            fused_results = self.reciprocal_rank_fusion(
                result_lists=[dense_results, sparse_results],
                id_field="chunk_id"
            )
            results["fused_results"] = fused_results
            results["stats"]["fused_count"] = len(fused_results)
            logger.info(f"RRF fusion produced {len(fused_results)} results")
            
            # 4. Reranker (可选)
            if use_reranker and fused_results:
                logger.info("Reranking results...")
                final_results = self.reranker_service.rerank(
                    query=query,
                    documents=fused_results,
                    top_k=top_k,
                    content_field="content"
                )
            else:
                final_results = fused_results[:top_k]
            
            results["final_results"] = final_results
            results["stats"]["final_count"] = len(final_results)
            logger.info(f"Final results: {len(final_results)}")
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        return results
    
    def sync_bm25_index(self, paper_id: str, chunks: List[Dict[str, Any]]):
        """
        同步 BM25 索引（在索引论文时调用）
        
        Args:
            paper_id: 论文ID
            chunks: chunk 列表
        """
        self._get_services()
        self.bm25_service.add_documents(paper_id, chunks)
    
    def remove_from_bm25_index(self, paper_id: str):
        """
        从 BM25 索引中删除（在删除论文时调用）
        
        Args:
            paper_id: 论文ID
        """
        self._get_services()
        self.bm25_service.remove_documents(paper_id)


# 全局单例
_hybrid_service: Optional[HybridSearchService] = None


def get_hybrid_search_service() -> HybridSearchService:
    """获取混合检索服务单例"""
    global _hybrid_service
    if _hybrid_service is None:
        _hybrid_service = HybridSearchService()
    return _hybrid_service

