"""
Cross-Encoder Reranker 服务
使用 BGE-Reranker 或 Sentence-Transformers Cross-Encoder 进行重排序
"""
import logging
import os
from typing import List, Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# 模型配置
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
USE_GPU = os.getenv("USE_GPU", "false").lower() == "true"


class RerankerService:
    """Cross-Encoder Reranker 服务"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._initialized = False
        
    def _lazy_init(self):
        """延迟初始化模型（首次使用时加载）"""
        if self._initialized:
            return
            
        try:
            from sentence_transformers import CrossEncoder
            
            device = "cuda" if USE_GPU else "cpu"
            logger.info(f"Loading reranker model: {RERANKER_MODEL} on {device}")
            
            self.model = CrossEncoder(RERANKER_MODEL, device=device)
            self._initialized = True
            
            logger.info(f"✓ Reranker model loaded: {RERANKER_MODEL}")
            
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback reranker")
            self._initialized = True
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            self._initialized = True
            self.model = None
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        content_field: str = "content"
    ) -> List[Dict[str, Any]]:
        """
        使用 Cross-Encoder 重排序文档
        
        Args:
            query: 查询文本
            documents: 文档列表，每个文档需要包含 content_field 指定的字段
            top_k: 返回的文档数量（None 表示返回全部）
            content_field: 文档中内容字段的名称
            
        Returns:
            重排序后的文档列表，添加了 rerank_score 字段
        """
        if not documents:
            return []
        
        self._lazy_init()
        
        if self.model is None:
            # Fallback: 使用原有分数排序
            logger.warning("Reranker model not available, using fallback")
            return self._fallback_rerank(documents, top_k)
        
        try:
            # 构建 query-document pairs
            pairs = []
            for doc in documents:
                content = doc.get(content_field, "")
                if content:
                    pairs.append([query, content])
                else:
                    pairs.append([query, ""])
            
            # 计算 Cross-Encoder 分数
            scores = self.model.predict(pairs)
            
            # 添加分数到文档
            for i, doc in enumerate(documents):
                doc['rerank_score'] = float(scores[i])
            
            # 按 rerank_score 排序
            sorted_docs = sorted(documents, key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            # 返回 Top-K
            if top_k:
                sorted_docs = sorted_docs[:top_k]
            
            logger.info(f"Reranked {len(documents)} documents, returning {len(sorted_docs)}")
            return sorted_docs
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return self._fallback_rerank(documents, top_k)
    
    def _fallback_rerank(
        self, 
        documents: List[Dict[str, Any]], 
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback 重排序：使用现有分数
        """
        # 尝试使用现有的分数字段
        score_fields = ['relevance_score', 'bm25_score', 'rrf_score', 'score']
        
        for field in score_fields:
            if documents and field in documents[0]:
                sorted_docs = sorted(documents, key=lambda x: x.get(field, 0), reverse=True)
                for doc in sorted_docs:
                    doc['rerank_score'] = doc.get(field, 0)
                if top_k:
                    sorted_docs = sorted_docs[:top_k]
                return sorted_docs
        
        # 没有分数字段，保持原序
        for doc in documents:
            doc['rerank_score'] = 0.0
        
        if top_k:
            documents = documents[:top_k]
        
        return documents


# 全局单例
_reranker_service: Optional[RerankerService] = None


def get_reranker_service() -> RerankerService:
    """获取 Reranker 服务单例"""
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = RerankerService()
    return _reranker_service

