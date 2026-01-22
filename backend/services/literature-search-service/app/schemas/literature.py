"""
Literature schemas for OpenAlex API integration
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Author(BaseModel):
    """Author information"""
    id: Optional[str] = None
    name: Optional[str] = "Unknown"
    orcid: Optional[str] = None


class Institution(BaseModel):
    """Institution information"""
    id: Optional[str] = None
    name: Optional[str] = "Unknown"
    country: Optional[str] = None
    type: Optional[str] = None


class Concept(BaseModel):
    """Research concept/topic"""
    id: Optional[str] = None
    display_name: Optional[str] = "Unknown"
    level: int = 0
    score: float = 0.0


class OpenAccess(BaseModel):
    """Open access information"""
    is_oa: bool
    oa_status: Optional[str] = None
    oa_url: Optional[str] = None


class Work(BaseModel):
    """Academic work (paper) information"""
    id: Optional[str] = None
    title: Optional[str] = "Untitled"
    publication_year: Optional[int] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    abstract_inverted_index: Optional[Dict[str, List[int]]] = None
    cited_by_count: int = 0
    authors: List[Author] = []
    institutions: List[Institution] = []
    concepts: List[Concept] = []
    open_access: Optional[OpenAccess] = None
    pdf_url: Optional[str] = None
    type: Optional[str] = None
    venue: Optional[str] = None
    venue_issn: Optional[str] = None
    language: Optional[str] = None
    
    # URLs
    openalex_url: Optional[str] = None
    doi_url: Optional[str] = None


class SearchFilters(BaseModel):
    """Search filters"""
    publication_year_start: Optional[int] = None
    publication_year_end: Optional[int] = None
    min_cited_by_count: Optional[int] = None
    max_cited_by_count: Optional[int] = None
    open_access_only: Optional[bool] = None
    work_type: Optional[str] = None
    language: Optional[str] = None


class SearchRequest(BaseModel):
    """Literature search request"""
    query: str = Field(..., min_length=1, description="Search query")
    filters: Optional[SearchFilters] = None
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Results per page")
    sort: str = Field(default="relevance", description="Sort by: relevance, cited_by_count, publication_date")


class SearchResponse(BaseModel):
    """Literature search response"""
    results: List[Work]
    total: int
    page: int
    per_page: int
    total_pages: int


class SummarizeRequest(BaseModel):
    """Request to summarize a work"""
    work_id: str
    language: str = Field(default="zh", description="Summary language: zh, en")


class SummarizeResponse(BaseModel):
    """Summarized work response"""
    work_id: str
    title: str
    summary: Dict[str, str] = Field(
        description="Structured summary with keys: background, method, findings, significance"
    )


class ExportFormat(BaseModel):
    """Export format request"""
    work_ids: List[str] = Field(..., min_length=1)
    format: str = Field(default="bibtex", description="Export format: bibtex, ris, apa, mla")


class ExportResponse(BaseModel):
    """Export response"""
    format: str
    content: str

