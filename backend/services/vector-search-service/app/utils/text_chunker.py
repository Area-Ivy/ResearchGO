"""
文本切分工具 - 用于将长文本切分成适合向量化的chunks
"""
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    max_chunks: int = 100
) -> List[Dict[str, Any]]:
    """
    将文本切分成chunks
    
    Args:
        text: 输入文本
        chunk_size: chunk大小（字符数）
        chunk_overlap: 重叠大小（字符数）
        max_chunks: 最大chunk数量
        
    Returns:
        List[Dict]: chunk列表，每个包含text, chunk_index, start_pos, end_pos, total_chars
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for chunking")
        return []
    
    # 清理文本
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 如果文本短于chunk_size，直接返回整个文本
    if len(text) <= chunk_size:
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
    
    while start < len(text) and chunk_index < max_chunks:
        # 计算当前chunk的结束位置
        end = start + chunk_size
        
        # 如果不是最后一个chunk，尝试在合适的位置断开
        if end < len(text):
            # 在句号、换行符等位置断开
            end = _find_split_point(text, start, end)
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
        start = end - chunk_overlap
        
        # 确保不会向后移动
        if chunks and start <= chunks[-1]['start_pos']:
            start = end
    
    logger.info(f"Split text into {len(chunks)} chunks (total: {len(text)} chars)")
    return chunks


def _find_split_point(text: str, start: int, end: int) -> int:
    """找到合适的切分点"""
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
