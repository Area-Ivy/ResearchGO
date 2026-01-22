"""
Literature API endpoints
Provides REST API for academic literature search using OpenAlex
"""
import logging
import json
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.schemas.literature import (
    SearchRequest, SearchResponse, Work,
    SummarizeRequest, SummarizeResponse,
    ExportFormat, ExportResponse
)
from app.services.openalex_service import get_openalex_service
from app.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/literature", tags=["literature"])


@router.post("/search", response_model=SearchResponse)
async def search_literature(request: SearchRequest):
    """
    Search for academic literature using OpenAlex API
    
    Query examples:
    - "machine learning"
    - "neural networks deep learning"
    - "climate change impacts"
    """
    try:
        logger.info(f"Literature search request: query='{request.query}', page={request.page}")
        
        result = await get_openalex_service().search_works(
            query=request.query,
            filters=request.filters,
            page=request.page,
            per_page=request.per_page,
            sort=request.sort
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in literature search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search literature: {str(e)}"
        )


@router.get("/work/{work_id}", response_model=Work)
async def get_work_detail(work_id: str):
    """
    Get detailed information about a specific work
    
    Args:
        work_id: OpenAlex work ID (e.g., 'W2741809807')
    """
    try:
        logger.info(f"Fetching work detail: {work_id}")
        
        work = await get_openalex_service().get_work_detail(work_id)
        
        return work
        
    except Exception as e:
        logger.error(f"Error fetching work {work_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work not found: {work_id}"
        )


@router.get("/related/{work_id}", response_model=List[Work])
async def get_related_works(work_id: str, limit: int = 10):
    """
    Get related works based on concepts and citations
    
    Args:
        work_id: OpenAlex work ID
        limit: Maximum number of related works (default: 10)
    """
    try:
        logger.info(f"Fetching related works for: {work_id}")
        
        related_works = await get_openalex_service().get_related_works(work_id, limit)
        
        return related_works
        
    except Exception as e:
        logger.error(f"Error fetching related works: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch related works: {str(e)}"
        )


@router.get("/author/{author_id}")
async def get_author_info(author_id: str):
    """
    Get author information
    
    Args:
        author_id: OpenAlex author ID
    """
    try:
        logger.info(f"Fetching author info: {author_id}")
        
        author_info = await get_openalex_service().get_author_info(author_id)
        
        return author_info
        
    except Exception as e:
        logger.error(f"Error fetching author: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author not found: {author_id}"
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_work(request: SummarizeRequest):
    """
    Generate AI summary of a work
    
    Uses OpenAI to generate a structured summary in the specified language
    """
    try:
        logger.info(f"Generating summary for work: {request.work_id}")
        
        # First, get the work details
        work = await get_openalex_service().get_work_detail(request.work_id)
        
        # Check if abstract exists
        if not work.abstract or len(work.abstract.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Work does not have sufficient abstract for summarization"
            )
        
        # Prepare prompt for OpenAI
        language_name = "中文" if request.language == "zh" else "English"
        prompt = f"""请分析以下学术论文并生成结构化摘要（使用{language_name}）：

标题：{work.title}
作者：{', '.join([a.name for a in work.authors[:5]])}
年份：{work.publication_year or 'Unknown'}
引用数：{work.cited_by_count}

摘要：
{work.abstract}

请按以下结构生成摘要：
1. 研究背景 (Background)
2. 研究方法 (Method)
3. 核心发现 (Findings)
4. 研究意义 (Significance)

要求：
- 每个部分2-3句话
- 简洁准确
- 突出重点
- 使用{language_name}

请严格按照JSON格式返回：
{{
    "background": "...",
    "method": "...",
    "findings": "...",
    "significance": "..."
}}
"""
        
        # Call OpenAI
        messages = [
            {"role": "system", "content": f"你是一个专业的学术论文分析助手，擅长生成结构化的论文摘要。请使用{language_name}回复。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await get_openai_service().chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=800
        )
        
        # Parse JSON response
        try:
            summary_dict = json.loads(response)
        except json.JSONDecodeError:
            # If not valid JSON, try to extract content
            logger.warning("OpenAI response is not valid JSON, using raw response")
            summary_dict = {
                "background": response[:200],
                "method": "",
                "findings": "",
                "significance": ""
            }
        
        logger.info(f"Successfully generated summary for {request.work_id}")
        
        return SummarizeResponse(
            work_id=work.id,
            title=work.title,
            summary=summary_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post("/export", response_model=ExportResponse)
async def export_citations(request: ExportFormat):
    """
    Export citations in various formats
    
    Supported formats:
    - bibtex: BibTeX format
    - ris: RIS format
    - apa: APA style
    - mla: MLA style
    """
    try:
        logger.info(f"Exporting {len(request.work_ids)} works in {request.format} format")
        
        # Fetch all works
        works = []
        for work_id in request.work_ids:
            try:
                work = await get_openalex_service().get_work_detail(work_id)
                works.append(work)
            except Exception as e:
                logger.warning(f"Failed to fetch work {work_id}: {e}")
                continue
        
        if not works:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid works to export"
            )
        
        # Generate citations based on format
        if request.format == "bibtex":
            content = _generate_bibtex(works)
        elif request.format == "ris":
            content = _generate_ris(works)
        elif request.format == "apa":
            content = _generate_apa(works)
        elif request.format == "mla":
            content = _generate_mla(works)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {request.format}"
            )
        
        logger.info(f"Successfully exported {len(works)} works")
        
        return ExportResponse(
            format=request.format,
            content=content
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting citations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export citations: {str(e)}"
        )


def _generate_bibtex(works: List[Work]) -> str:
    """Generate BibTeX format citations"""
    entries = []
    
    for work in works:
        # Generate citation key
        first_author = work.authors[0].name.split()[-1] if work.authors else "Unknown"
        year = work.publication_year or "n.d."
        key = f"{first_author}{year}"
        
        # Get authors
        authors = " and ".join([a.name for a in work.authors])
        
        # Build entry
        entry = f"""@article{{{key},
  title = {{{work.title}}},
  author = {{{authors}}},
  year = {{{year}}},
  journal = {{{work.venue or 'Unknown'}}},
  doi = {{{work.doi or ''}}},
  url = {{{work.doi_url or work.openalex_url or ''}}}
}}"""
        entries.append(entry)
    
    return "\n\n".join(entries)


def _generate_ris(works: List[Work]) -> str:
    """Generate RIS format citations"""
    entries = []
    
    for work in works:
        lines = ["TY  - JOUR"]
        lines.append(f"TI  - {work.title}")
        
        for author in work.authors:
            lines.append(f"AU  - {author.name}")
        
        if work.publication_year:
            lines.append(f"PY  - {work.publication_year}")
        
        if work.venue:
            lines.append(f"JO  - {work.venue}")
        
        if work.doi:
            lines.append(f"DO  - {work.doi}")
        
        if work.doi_url:
            lines.append(f"UR  - {work.doi_url}")
        
        lines.append("ER  -")
        entries.append("\n".join(lines))
    
    return "\n\n".join(entries)


def _generate_apa(works: List[Work]) -> str:
    """Generate APA style citations"""
    citations = []
    
    for work in works:
        # Authors
        if work.authors:
            if len(work.authors) == 1:
                authors_str = work.authors[0].name
            elif len(work.authors) <= 20:
                authors_str = ", ".join([a.name for a in work.authors[:-1]]) + f", & {work.authors[-1].name}"
            else:
                authors_str = ", ".join([a.name for a in work.authors[:19]]) + ", ... " + work.authors[-1].name
        else:
            authors_str = "Unknown"
        
        # Year
        year = work.publication_year or "n.d."
        
        # Title
        title = work.title
        
        # Journal
        journal = work.venue or "Unknown Journal"
        
        # DOI
        doi_part = f" https://doi.org/{work.doi}" if work.doi else ""
        
        citation = f"{authors_str} ({year}). {title}. {journal}.{doi_part}"
        citations.append(citation)
    
    return "\n\n".join(citations)


def _generate_mla(works: List[Work]) -> str:
    """Generate MLA style citations"""
    citations = []
    
    for work in works:
        # First author (Last, First)
        if work.authors:
            first_author = work.authors[0].name
            # Simple name reversal (not perfect but good enough)
            name_parts = first_author.split()
            if len(name_parts) >= 2:
                first_author_mla = f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"
            else:
                first_author_mla = first_author
            
            if len(work.authors) > 1:
                authors_str = f"{first_author_mla}, et al."
            else:
                authors_str = first_author_mla
        else:
            authors_str = "Unknown"
        
        # Title in quotes
        title = f'"{work.title}"'
        
        # Journal in italics (we'll use underscores)
        journal = f"_{work.venue or 'Unknown Journal'}_" if work.venue else ""
        
        # Year
        year = work.publication_year or "n.d."
        
        # DOI
        doi_part = f" doi:{work.doi}" if work.doi else ""
        
        citation = f"{authors_str}. {title}. {journal}, {year}.{doi_part}"
        citations.append(citation)
    
    return "\n\n".join(citations)


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "literature-search-service",
        "provider": "OpenAlex"
    }

