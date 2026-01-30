"""
LLM 论文结构解析器
使用 GPT 提取论文的结构化信息
"""
import os
import json
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@dataclass
class PaperSection:
    """论文章节"""
    section_type: str      # abstract, introduction, methods, results, discussion, conclusion, other
    section_title: str     # 章节标题
    content: str           # 章节内容
    page_start: int = 0    # 起始页（如果可用）
    subsections: List['PaperSection'] = None
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []
    
    def to_dict(self) -> dict:
        return {
            'section_type': self.section_type,
            'section_title': self.section_title,
            'content': self.content,
            'page_start': self.page_start,
            'subsections': [s.to_dict() for s in self.subsections] if self.subsections else []
        }


@dataclass
class PaperStructure:
    """论文结构"""
    title: str
    authors: List[str]
    abstract: str
    sections: List[PaperSection]
    references_count: int = 0
    
    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'sections': [s.to_dict() for s in self.sections],
            'references_count': self.references_count
        }


class PaperStructureParser:
    """LLM 论文结构解析器"""
    
    # 标准章节类型映射
    SECTION_TYPE_MAP = {
        'abstract': ['abstract', '摘要'],
        'introduction': ['introduction', 'background', '引言', '背景', '绪论'],
        'related_work': ['related work', 'literature review', '相关工作', '文献综述'],
        'methods': ['method', 'methodology', 'approach', 'model', 'framework', '方法', '模型'],
        'experiments': ['experiment', 'evaluation', 'setup', '实验', '实验设置'],
        'results': ['result', 'finding', '结果', '实验结果'],
        'discussion': ['discussion', 'analysis', '讨论', '分析'],
        'conclusion': ['conclusion', 'summary', 'future work', '结论', '总结'],
        'references': ['reference', 'bibliography', '参考文献'],
        'appendix': ['appendix', '附录']
    }
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = os.getenv('OPENAI_BASE_URL')
        
        client_kwargs = {
            'api_key': self.api_key,
            'timeout': 120.0
        }
        if self.base_url:
            client_kwargs['base_url'] = self.base_url
            
        self.client = AsyncOpenAI(**client_kwargs)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    
    def _classify_section_type(self, title: str) -> str:
        """根据标题分类章节类型"""
        title_lower = title.lower().strip()
        
        for section_type, keywords in self.SECTION_TYPE_MAP.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return section_type
        
        return 'other'
    
    async def parse_structure(self, text: str, max_chars: int = 50000) -> PaperStructure:
        """
        使用 LLM 解析论文结构
        
        Args:
            text: 论文原始文本
            max_chars: 发送给 LLM 的最大字符数
            
        Returns:
            PaperStructure: 解析后的论文结构
        """
        # 截断过长的文本
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[文本已截断...]"
        
        system_prompt = """You are an expert academic paper parser. Your task is to extract the structure of a research paper.

Extract the following information in JSON format:
{
    "title": "Paper title",
    "authors": ["Author 1", "Author 2"],
    "abstract": "Full abstract text",
    "sections": [
        {
            "section_type": "introduction|methods|results|discussion|conclusion|related_work|experiments|other",
            "section_title": "Section Title",
            "content": "Section content text",
            "subsections": [
                {
                    "section_type": "...",
                    "section_title": "Subsection Title",
                    "content": "..."
                }
            ]
        }
    ],
    "references_count": 42
}

Rules:
1. section_type must be one of: introduction, related_work, methods, experiments, results, discussion, conclusion, other
2. Keep the full content of each section (don't summarize)
3. Identify subsections when they exist (e.g., "3.1 Data Collection")
4. Extract the abstract completely
5. Count the number of references (approximate is fine)
6. If a section doesn't fit standard categories, use "other"
7. Preserve the original text, don't translate or modify it"""

        user_prompt = f"""Parse the following academic paper and extract its structure:

---
{text}
---

Return ONLY valid JSON, no explanation."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=8000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # 构建 PaperStructure
            sections = []
            for s in result.get('sections', []):
                subsections = []
                for sub in s.get('subsections', []):
                    subsections.append(PaperSection(
                        section_type=sub.get('section_type', 'other'),
                        section_title=sub.get('section_title', ''),
                        content=sub.get('content', ''),
                        subsections=[]
                    ))
                
                sections.append(PaperSection(
                    section_type=s.get('section_type', 'other'),
                    section_title=s.get('section_title', ''),
                    content=s.get('content', ''),
                    subsections=subsections
                ))
            
            paper_structure = PaperStructure(
                title=result.get('title', 'Unknown'),
                authors=result.get('authors', []),
                abstract=result.get('abstract', ''),
                sections=sections,
                references_count=result.get('references_count', 0)
            )
            
            logger.info(f"✓ 论文结构解析完成: {paper_structure.title}")
            logger.info(f"  - 章节数: {len(sections)}")
            logger.info(f"  - 参考文献: {paper_structure.references_count}")
            
            return paper_structure
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            return self._fallback_parse(text)
        except Exception as e:
            logger.error(f"LLM 结构解析失败: {e}")
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> PaperStructure:
        """
        规则回退解析（当 LLM 失败时）
        """
        logger.info("使用规则回退解析...")
        
        # 简单的标题提取（通常是第一行）
        lines = text.strip().split('\n')
        title = lines[0] if lines else "Unknown"
        
        # 尝试提取摘要
        abstract = ""
        abstract_match = re.search(
            r'(?:Abstract|ABSTRACT|摘要)[:\s]*\n?([\s\S]*?)(?=\n(?:1\.|I\.|Introduction|INTRODUCTION|引言|Keywords|关键词))',
            text,
            re.IGNORECASE
        )
        if abstract_match:
            abstract = abstract_match.group(1).strip()
        
        # 按常见的章节标记分割
        section_pattern = r'\n(?=(?:\d+\.?\s+|[IVX]+\.?\s+)?(?:Introduction|Methods?|Results?|Discussion|Conclusion|Related Work|Experiments?|Background|引言|方法|结果|讨论|结论))'
        
        parts = re.split(section_pattern, text, flags=re.IGNORECASE)
        
        sections = []
        for part in parts[1:]:  # 跳过第一部分（通常是标题和摘要）
            # 提取章节标题（第一行）
            part_lines = part.strip().split('\n')
            if part_lines:
                section_title = part_lines[0].strip()
                section_content = '\n'.join(part_lines[1:]).strip()
                section_type = self._classify_section_type(section_title)
                
                sections.append(PaperSection(
                    section_type=section_type,
                    section_title=section_title,
                    content=section_content
                ))
        
        # 如果没有找到任何章节，把整个文本作为一个章节
        if not sections:
            sections.append(PaperSection(
                section_type='other',
                section_title='Full Text',
                content=text
            ))
        
        return PaperStructure(
            title=title,
            authors=[],
            abstract=abstract,
            sections=sections
        )


# 全局实例
_parser: Optional[PaperStructureParser] = None


def get_paper_structure_parser() -> PaperStructureParser:
    """获取论文结构解析器实例"""
    global _parser
    if _parser is None:
        _parser = PaperStructureParser()
    return _parser

