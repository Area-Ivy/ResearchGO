"""
文本切分工具
用于将长文本切分成适合向量化的chunks
"""
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TextChunker:
    """文本切分器"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_chunks: int = 100
    ):
        """
        初始化文本切分器
        
        Args:
            chunk_size: 每个chunk的字符数
            chunk_overlap: chunk之间的重叠字符数
            max_chunks: 每篇文档的最大chunk数量
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunks = max_chunks
        
    def split_text(self, text: str) -> List[Dict[str, Any]]:
        """
        将文本切分成chunks
        
        Args:
            text: 输入文本
            
        Returns:
            List[Dict]: chunk列表，每个包含text, start_pos, end_pos
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        # 清理文本
        text = self._clean_text(text)
        
        # 如果文本短于chunk_size，直接返回整个文本
        if len(text) <= self.chunk_size:
            return [{
                'text': text,
                'chunk_index': 0,
                'start_pos': 0,
                'end_pos': len(text),
                'total_chars': len(text)
            }]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text) and chunk_index < self.max_chunks:
            # 计算当前chunk的结束位置
            end = start + self.chunk_size
            
            # 如果不是最后一个chunk，尝试在合适的位置断开
            if end < len(text):
                # 在句号、换行符等位置断开
                end = self._find_split_point(text, start, end)
            else:
                end = len(text)
            
            # 提取chunk文本
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'chunk_index': chunk_index,
                    'start_pos': start,
                    'end_pos': end,
                    'total_chars': len(chunk_text)
                })
                chunk_index += 1
            
            # 移动到下一个chunk，考虑重叠
            start = end - self.chunk_overlap
            
            # 确保不会向后移动
            if start <= chunks[-1]['start_pos'] if chunks else 0:
                start = end
        
        logger.info(f"Split text into {len(chunks)} chunks (total: {len(text)} chars)")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本
        
        Args:
            text: 输入文本
            
        Returns:
            str: 清理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留基本标点）
        # text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]，。！？；：、（）【】]', '', text)
        
        return text.strip()
    
    def _find_split_point(self, text: str, start: int, end: int) -> int:
        """
        找到合适的切分点
        
        优先级：
        1. 段落分隔符（\n\n）
        2. 句子结束符（。！？.!?）
        3. 逗号或分号（，；,;）
        4. 空格
        
        Args:
            text: 文本
            start: 起始位置
            end: 期望的结束位置
            
        Returns:
            int: 实际的切分位置
        """
        # 向后查找窗口（最多再往后看100个字符）
        search_end = min(end + 100, len(text))
        search_text = text[end:search_end]
        
        # 1. 查找段落分隔符
        paragraph_break = search_text.find('\n\n')
        if paragraph_break != -1:
            return end + paragraph_break + 2
        
        # 2. 查找句子结束符
        sentence_ends = []
        for pattern in ['。', '！', '？', '.', '!', '?']:
            pos = search_text.find(pattern)
            if pos != -1:
                sentence_ends.append(pos)
        
        if sentence_ends:
            return end + min(sentence_ends) + 1
        
        # 3. 查找逗号或分号
        comma_pos = -1
        for pattern in ['，', '；', ',', ';']:
            pos = search_text.find(pattern)
            if pos != -1 and (comma_pos == -1 or pos < comma_pos):
                comma_pos = pos
        
        if comma_pos != -1:
            return end + comma_pos + 1
        
        # 4. 查找空格
        space_pos = search_text.find(' ')
        if space_pos != -1:
            return end + space_pos + 1
        
        # 如果都没找到，就在原位置切分
        return end
    
    def split_by_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """
        按段落切分文本（用于结构化文档）
        
        Args:
            text: 输入文本
            
        Returns:
            List[Dict]: chunk列表
        """
        # 按双换行符切分段落
        paragraphs = re.split(r'\n\n+', text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        start_pos = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前chunk + 新段落不超过chunk_size，就合并
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 保存当前chunk
                if current_chunk:
                    chunks.append({
                        'text': current_chunk,
                        'chunk_index': chunk_index,
                        'start_pos': start_pos,
                        'end_pos': start_pos + len(current_chunk),
                        'total_chars': len(current_chunk)
                    })
                    chunk_index += 1
                    start_pos += len(current_chunk) + 2
                
                # 如果单个段落超过chunk_size，需要进一步切分
                if len(para) > self.chunk_size:
                    para_chunks = self.split_text(para)
                    for pc in para_chunks:
                        pc['chunk_index'] = chunk_index
                        chunks.append(pc)
                        chunk_index += 1
                    current_chunk = ""
                else:
                    current_chunk = para
            
            # 限制chunk数量
            if chunk_index >= self.max_chunks:
                break
        
        # 添加最后一个chunk
        if current_chunk and chunk_index < self.max_chunks:
            chunks.append({
                'text': current_chunk,
                'chunk_index': chunk_index,
                'start_pos': start_pos,
                'end_pos': start_pos + len(current_chunk),
                'total_chars': len(current_chunk)
            })
        
        logger.info(f"Split text into {len(chunks)} paragraph-based chunks")
        return chunks


# 创建默认实例
default_chunker = TextChunker(
    chunk_size=1000,
    chunk_overlap=200,
    max_chunks=100
)


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    max_chunks: int = 100,
    method: str = "sliding_window"
) -> List[Dict[str, Any]]:
    """
    便捷函数：将文本切分成chunks
    
    Args:
        text: 输入文本
        chunk_size: chunk大小
        chunk_overlap: 重叠大小
        max_chunks: 最大chunk数
        method: 切分方法 ("sliding_window" 或 "paragraphs")
        
    Returns:
        List[Dict]: chunk列表
    """
    chunker = TextChunker(chunk_size, chunk_overlap, max_chunks)
    
    if method == "paragraphs":
        return chunker.split_by_paragraphs(text)
    else:
        return chunker.split_text(text)

