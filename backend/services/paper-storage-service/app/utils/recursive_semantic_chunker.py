"""
递归语义切分器
基于论文结构进行递归语义切分
"""
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StructuredChunk:
    """结构化的 Chunk"""
    content: str                    # 文本内容
    chunk_index: int                # chunk 索引
    section_type: str               # 章节类型: abstract, introduction, methods, results, discussion, conclusion, other
    section_title: str              # 章节标题
    subsection_title: Optional[str] # 子章节标题（如果有）
    hierarchy_path: str             # 层级路径，如 "Methods > Data Collection"
    char_count: int                 # 字符数
    is_complete_section: bool       # 是否是完整的章节（未被切分）
    
    def to_dict(self) -> dict:
        return {
            'content': self.content,
            'chunk_index': self.chunk_index,
            'section_type': self.section_type,
            'section_title': self.section_title,
            'subsection_title': self.subsection_title,
            'hierarchy_path': self.hierarchy_path,
            'char_count': self.char_count,
            'is_complete_section': self.is_complete_section
        }


class RecursiveSemanticChunker:
    """
    递归语义切分器
    
    策略:
    1. 首先按章节结构切分
    2. 如果章节内容超过 max_chunk_size，递归按语义边界切分
    3. 语义边界优先级: 段落 > 句子 > 子句 > 硬切分
    """
    
    # 分隔符优先级（从高到低）
    SEPARATORS = [
        ("\n\n", "paragraph"),      # 段落
        ("\n", "line"),             # 行
        ("。", "sentence_zh"),      # 中文句子
        (". ", "sentence_en"),      # 英文句子
        ("；", "clause_zh"),        # 中文分句
        ("; ", "clause_en"),        # 英文分句
        ("，", "comma_zh"),         # 中文逗号
        (", ", "comma_en"),         # 英文逗号
        (" ", "word"),              # 单词
    ]
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        chunk_overlap: int = 100
    ):
        """
        Args:
            max_chunk_size: 最大 chunk 大小（字符数）
            min_chunk_size: 最小 chunk 大小（避免过小的 chunk）
            chunk_overlap: chunk 之间的重叠字符数
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_paper(self, paper_structure: dict) -> List[StructuredChunk]:
        """
        对论文进行结构化切分
        
        Args:
            paper_structure: 论文结构（来自 PaperStructureParser）
            
        Returns:
            List[StructuredChunk]: 结构化的 chunk 列表
        """
        chunks = []
        chunk_index = 0
        
        # 1. 处理摘要
        abstract = paper_structure.get('abstract', '')
        if abstract:
            abstract_chunks = self._recursive_split(
                text=abstract,
                section_type='abstract',
                section_title='Abstract',
                subsection_title=None,
                hierarchy_path='Abstract'
            )
            for chunk_content, is_complete in abstract_chunks:
                chunks.append(StructuredChunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    section_type='abstract',
                    section_title='Abstract',
                    subsection_title=None,
                    hierarchy_path='Abstract',
                    char_count=len(chunk_content),
                    is_complete_section=is_complete
                ))
                chunk_index += 1
        
        # 2. 处理各个章节
        for section in paper_structure.get('sections', []):
            section_type = section.get('section_type', 'other')
            section_title = section.get('section_title', '')
            section_content = section.get('content', '')
            subsections = section.get('subsections', [])
            
            # 如果章节有内容（不只是子章节），先处理章节内容
            if section_content.strip():
                section_chunks = self._recursive_split(
                    text=section_content,
                    section_type=section_type,
                    section_title=section_title,
                    subsection_title=None,
                    hierarchy_path=section_title
                )
                for chunk_content, is_complete in section_chunks:
                    chunks.append(StructuredChunk(
                        content=chunk_content,
                        chunk_index=chunk_index,
                        section_type=section_type,
                        section_title=section_title,
                        subsection_title=None,
                        hierarchy_path=section_title,
                        char_count=len(chunk_content),
                        is_complete_section=is_complete
                    ))
                    chunk_index += 1
            
            # 处理子章节
            for subsection in subsections:
                sub_type = subsection.get('section_type', section_type)
                sub_title = subsection.get('section_title', '')
                sub_content = subsection.get('content', '')
                hierarchy_path = f"{section_title} > {sub_title}"
                
                if sub_content.strip():
                    sub_chunks = self._recursive_split(
                        text=sub_content,
                        section_type=sub_type,
                        section_title=section_title,
                        subsection_title=sub_title,
                        hierarchy_path=hierarchy_path
                    )
                    for chunk_content, is_complete in sub_chunks:
                        chunks.append(StructuredChunk(
                            content=chunk_content,
                            chunk_index=chunk_index,
                            section_type=sub_type,
                            section_title=section_title,
                            subsection_title=sub_title,
                            hierarchy_path=hierarchy_path,
                            char_count=len(chunk_content),
                            is_complete_section=is_complete
                        ))
                        chunk_index += 1
        
        logger.info(f"✓ 递归语义切分完成: {len(chunks)} 个 chunks")
        
        # 统计信息
        section_types = {}
        for chunk in chunks:
            section_types[chunk.section_type] = section_types.get(chunk.section_type, 0) + 1
        logger.info(f"  - 章节分布: {section_types}")
        
        return chunks
    
    def _recursive_split(
        self,
        text: str,
        section_type: str,
        section_title: str,
        subsection_title: Optional[str],
        hierarchy_path: str,
        separator_index: int = 0
    ) -> List[tuple]:
        """
        递归切分文本
        
        Returns:
            List[tuple]: [(chunk_content, is_complete_section), ...]
        """
        text = text.strip()
        
        # 如果文本足够短，直接返回
        if len(text) <= self.max_chunk_size:
            return [(text, True)]
        
        # 如果已经用完所有分隔符，硬切分
        if separator_index >= len(self.SEPARATORS):
            return self._hard_split(text)
        
        separator, sep_name = self.SEPARATORS[separator_index]
        
        # 按当前分隔符切分
        parts = text.split(separator)
        
        # 如果只有一个部分，尝试下一个分隔符
        if len(parts) <= 1:
            return self._recursive_split(
                text, section_type, section_title, subsection_title,
                hierarchy_path, separator_index + 1
            )
        
        # 合并小片段
        chunks = []
        current_chunk = ""
        
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            
            # 加上分隔符（除了最后一个）
            part_with_sep = part + separator if i < len(parts) - 1 else part
            
            # 如果当前 chunk + 新部分不超过限制
            if len(current_chunk) + len(part_with_sep) <= self.max_chunk_size:
                current_chunk += part_with_sep
            else:
                # 保存当前 chunk
                if current_chunk.strip():
                    # 如果当前 chunk 还是太大，递归处理
                    if len(current_chunk) > self.max_chunk_size:
                        sub_chunks = self._recursive_split(
                            current_chunk, section_type, section_title, 
                            subsection_title, hierarchy_path, separator_index + 1
                        )
                        chunks.extend(sub_chunks)
                    else:
                        chunks.append((current_chunk.strip(), False))
                
                # 开始新 chunk（带重叠）
                if self.chunk_overlap > 0 and current_chunk:
                    # 从当前 chunk 末尾取一部分作为重叠
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + part_with_sep
                else:
                    current_chunk = part_with_sep
        
        # 处理最后一个 chunk
        if current_chunk.strip():
            if len(current_chunk) > self.max_chunk_size:
                sub_chunks = self._recursive_split(
                    current_chunk, section_type, section_title, 
                    subsection_title, hierarchy_path, separator_index + 1
                )
                chunks.extend(sub_chunks)
            else:
                chunks.append((current_chunk.strip(), False))
        
        return chunks
    
    def _hard_split(self, text: str) -> List[tuple]:
        """
        硬切分（最后的手段）
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.max_chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append((chunk, False))
            start = end - self.chunk_overlap if self.chunk_overlap > 0 else end
        
        return chunks


def chunk_structured_paper(
    paper_structure: dict,
    max_chunk_size: int = 1000,
    min_chunk_size: int = 100,
    chunk_overlap: int = 100
) -> List[StructuredChunk]:
    """
    便捷函数：对论文进行结构化切分
    
    Args:
        paper_structure: 论文结构（来自 PaperStructureParser.to_dict()）
        max_chunk_size: 最大 chunk 大小
        min_chunk_size: 最小 chunk 大小
        chunk_overlap: chunk 重叠
        
    Returns:
        List[StructuredChunk]: 结构化的 chunk 列表
    """
    chunker = RecursiveSemanticChunker(
        max_chunk_size=max_chunk_size,
        min_chunk_size=min_chunk_size,
        chunk_overlap=chunk_overlap
    )
    return chunker.chunk_paper(paper_structure)

