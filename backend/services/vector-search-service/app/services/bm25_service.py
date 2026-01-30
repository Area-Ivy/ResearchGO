"""
BM25 稀疏检索服务
用于混合检索中的关键词匹配
"""
import logging
import re
import jieba
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from collections import defaultdict

logger = logging.getLogger(__name__)


class BM25Service:
    """BM25 稀疏检索服务"""
    
    def __init__(self):
        self.corpus: Dict[str, List[str]] = {}  # paper_id -> tokenized chunks
        self.chunk_map: Dict[str, List[Dict]] = {}  # paper_id -> chunk metadata
        self.bm25_index: Dict[str, BM25Okapi] = {}  # paper_id -> BM25 index
        self.global_corpus: List[str] = []  # 全局语料（tokenized）
        self.global_chunk_map: List[Dict] = []  # 全局 chunk 元数据
        self.global_bm25: Optional[BM25Okapi] = None
        
    def tokenize(self, text: str) -> List[str]:
        """
        分词（支持中英文）
        """
        # 清理文本
        text = text.lower()
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        
        # 使用 jieba 分词（支持中文）
        tokens = list(jieba.cut(text))
        
        # 过滤停用词和短词
        tokens = [t.strip() for t in tokens if len(t.strip()) > 1]
        
        return tokens
    
    def add_documents(
        self, 
        paper_id: str, 
        chunks: List[Dict[str, Any]]
    ):
        """
        添加文档到 BM25 索引
        
        Args:
            paper_id: 论文ID
            chunks: chunk 列表，每个包含 content, chunk_id 等
        """
        try:
            tokenized_chunks = []
            chunk_metadata = []
            
            for chunk in chunks:
                content = chunk.get('content', '')
                tokens = self.tokenize(content)
                
                if tokens:
                    tokenized_chunks.append(tokens)
                    chunk_metadata.append({
                        'paper_id': paper_id,
                        'chunk_id': chunk.get('chunk_id', ''),
                        'chunk_index': chunk.get('chunk_index', 0),
                        'content': content,
                        'title': chunk.get('title', ''),
                        'file_name': chunk.get('file_name', ''),
                    })
            
            if tokenized_chunks:
                # 构建论文级别的 BM25 索引
                self.corpus[paper_id] = tokenized_chunks
                self.chunk_map[paper_id] = chunk_metadata
                self.bm25_index[paper_id] = BM25Okapi(tokenized_chunks)
                
                # 添加到全局索引
                self.global_corpus.extend(tokenized_chunks)
                self.global_chunk_map.extend(chunk_metadata)
                
                logger.info(f"✓ BM25 indexed {len(tokenized_chunks)} chunks for paper: {paper_id}")
                
        except Exception as e:
            logger.error(f"Failed to add documents to BM25: {e}")
    
    def rebuild_global_index(self):
        """重建全局 BM25 索引"""
        if self.global_corpus:
            self.global_bm25 = BM25Okapi(self.global_corpus)
            logger.info(f"✓ Global BM25 index rebuilt with {len(self.global_corpus)} chunks")
    
    def clear_all(self):
        """
        清空所有 BM25 索引
        """
        self.corpus = {}
        self.chunk_map = {}
        self.bm25_index = {}
        self.global_corpus = []
        self.global_chunk_map = []
        self.global_bm25 = None
        logger.info("✓ BM25 all indexes cleared")
    
    def remove_documents(self, paper_id: str):
        """
        从 BM25 索引中删除文档
        """
        try:
            if paper_id in self.corpus:
                # 从全局索引中移除
                chunks_to_remove = set()
                for i, meta in enumerate(self.global_chunk_map):
                    if meta['paper_id'] == paper_id:
                        chunks_to_remove.add(i)
                
                # 反向删除（避免索引问题）
                for i in sorted(chunks_to_remove, reverse=True):
                    self.global_corpus.pop(i)
                    self.global_chunk_map.pop(i)
                
                # 删除论文级别索引
                del self.corpus[paper_id]
                del self.chunk_map[paper_id]
                del self.bm25_index[paper_id]
                
                # 重建全局索引
                self.rebuild_global_index()
                
                logger.info(f"✓ BM25 removed documents for paper: {paper_id}")
                
        except Exception as e:
            logger.error(f"Failed to remove documents from BM25: {e}")
    
    def search(
        self, 
        query: str, 
        top_k: int = 10,
        paper_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        BM25 搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            paper_id: 限定在特定论文内搜索（可选）
            
        Returns:
            搜索结果列表
        """
        try:
            tokens = self.tokenize(query)
            
            if not tokens:
                logger.warning("Empty query after tokenization")
                return []
            
            if paper_id and paper_id in self.bm25_index:
                # 论文级别搜索
                bm25 = self.bm25_index[paper_id]
                chunk_map = self.chunk_map[paper_id]
            else:
                # 全局搜索
                if not self.global_bm25:
                    self.rebuild_global_index()
                if not self.global_bm25:
                    return []
                bm25 = self.global_bm25
                chunk_map = self.global_chunk_map
            
            # 计算 BM25 分数
            scores = bm25.get_scores(tokens)
            
            # 获取 Top-K
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # 只返回有分数的结果
                    result = chunk_map[idx].copy()
                    result['bm25_score'] = float(scores[idx])
                    results.append(result)
            
            logger.info(f"BM25 search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []


# 全局单例
_bm25_service: Optional[BM25Service] = None


def get_bm25_service() -> BM25Service:
    """获取 BM25 服务单例"""
    global _bm25_service
    if _bm25_service is None:
        _bm25_service = BM25Service()
    return _bm25_service

