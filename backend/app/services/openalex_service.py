"""
OpenAlex API Service
Handles all interactions with OpenAlex API
"""
import os
import logging
from typing import List, Optional, Dict, Any
import httpx
from app.models.literature import (
    Work, Author, Institution, Concept, OpenAccess,
    SearchFilters, SearchResponse
)

logger = logging.getLogger(__name__)


class OpenAlexService:
    """Service for interacting with OpenAlex API"""
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(self):
        self.email = os.getenv("CONTACT_EMAIL", "")
        self.headers = {
            "User-Agent": f"ResearchGO/1.0 (mailto:{self.email})" if self.email else "ResearchGO/1.0",
            "Accept": "application/json"
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        
    async def search_works(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        page: int = 1,
        per_page: int = 20,
        sort: str = "relevance"
    ) -> SearchResponse:
        """
        Search for academic works
        
        Args:
            query: Search query string
            filters: Optional filters
            page: Page number (1-indexed)
            per_page: Results per page
            sort: Sort order (relevance, cited_by_count, publication_date)
            
        Returns:
            SearchResponse with results
        """
        try:
            # Build filter string
            filter_parts = []
            if filters:
                if filters.publication_year_start and filters.publication_year_end:
                    filter_parts.append(
                        f"publication_year:{filters.publication_year_start}-{filters.publication_year_end}"
                    )
                elif filters.publication_year_start:
                    filter_parts.append(f"from_publication_date:{filters.publication_year_start}-01-01")
                elif filters.publication_year_end:
                    filter_parts.append(f"to_publication_date:{filters.publication_year_end}-12-31")
                    
                if filters.min_cited_by_count is not None:
                    filter_parts.append(f"cited_by_count:>{filters.min_cited_by_count}")
                    
                if filters.max_cited_by_count is not None:
                    filter_parts.append(f"cited_by_count:<{filters.max_cited_by_count}")
                    
                if filters.open_access_only:
                    filter_parts.append("is_oa:true")
                    
                if filters.work_type:
                    filter_parts.append(f"type:{filters.work_type}")
                    
                if filters.language:
                    filter_parts.append(f"language:{filters.language}")
            
            # Build sort parameter
            sort_param = {
                "relevance": "relevance_score:desc",
                "cited_by_count": "cited_by_count:desc",
                "publication_date": "publication_date:desc"
            }.get(sort, "relevance_score:desc")
            
            # Build request parameters
            params = {
                "search": query,
                "page": page,
                "per_page": per_page,
                "sort": sort_param
            }
            
            if filter_parts:
                params["filter"] = ",".join(filter_parts)
            
            logger.info(f"Searching OpenAlex with query='{query}', page={page}, filters={filter_parts}")
            
            # Make request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/works",
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
            
            # Parse results
            results = []
            for item in data.get("results", []):
                work = self._parse_work(item)
                results.append(work)
            
            # Calculate total pages
            total = data.get("meta", {}).get("count", 0)
            total_pages = (total + per_page - 1) // per_page
            
            logger.info(f"Found {total} works, returning page {page}/{total_pages}")
            
            return SearchResponse(
                results=results,
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching OpenAlex: {e}")
            raise Exception(f"OpenAlex API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error searching OpenAlex: {e}")
            raise Exception(f"Failed to search OpenAlex: {str(e)}")
    
    async def get_work_detail(self, work_id: str) -> Work:
        """
        Get detailed information about a work
        
        Args:
            work_id: OpenAlex work ID (e.g., 'W2741809807' or full URL)
            
        Returns:
            Work object with detailed information
        """
        try:
            # Extract ID if full URL provided
            if work_id.startswith("http"):
                work_id = work_id.split("/")[-1]
            
            logger.info(f"Fetching work detail for {work_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/works/{work_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
            
            work = self._parse_work(data)
            logger.info(f"Successfully fetched work: {work.title}")
            
            return work
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching work {work_id}: {e}")
            raise Exception(f"Work not found: {work_id}")
        except Exception as e:
            logger.error(f"Error fetching work {work_id}: {e}")
            raise Exception(f"Failed to fetch work: {str(e)}")
    
    async def get_related_works(self, work_id: str, limit: int = 10) -> List[Work]:
        """
        Get related works based on citations and concepts
        
        Args:
            work_id: OpenAlex work ID
            limit: Maximum number of related works
            
        Returns:
            List of related Work objects
        """
        try:
            # Extract ID if full URL provided
            if work_id.startswith("http"):
                work_id = work_id.split("/")[-1]
            
            logger.info(f"Fetching related works for {work_id}")
            
            # First get the work to extract concepts
            work = await self.get_work_detail(work_id)
            
            if not work.concepts:
                logger.warning(f"No concepts found for work {work_id}")
                return []
            
            # Use top concepts to find related works
            top_concepts = sorted(work.concepts, key=lambda c: c.score, reverse=True)[:3]
            concept_ids = [c.id.split("/")[-1] for c in top_concepts]
            
            # Search for works with similar concepts, excluding the original work
            params = {
                "filter": f"concepts.id:{'|'.join(concept_ids)},id:!{work_id}",
                "sort": "cited_by_count:desc",
                "per_page": limit
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/works",
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
            
            results = []
            for item in data.get("results", []):
                related_work = self._parse_work(item)
                results.append(related_work)
            
            logger.info(f"Found {len(results)} related works")
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching related works for {work_id}: {e}")
            return []
    
    async def get_author_info(self, author_id: str) -> Dict[str, Any]:
        """
        Get author information
        
        Args:
            author_id: OpenAlex author ID
            
        Returns:
            Dictionary with author information
        """
        try:
            # Extract ID if full URL provided
            if author_id.startswith("http"):
                author_id = author_id.split("/")[-1]
            
            logger.info(f"Fetching author info for {author_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/authors/{author_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
            
            author_info = {
                "id": data.get("id", ""),
                "name": data.get("display_name", ""),
                "orcid": data.get("orcid"),
                "works_count": data.get("works_count", 0),
                "cited_by_count": data.get("cited_by_count", 0),
                "h_index": data.get("summary_stats", {}).get("h_index", 0),
                "affiliations": [
                    inst.get("display_name", "") 
                    for inst in data.get("affiliations", [])
                ]
            }
            
            logger.info(f"Successfully fetched author: {author_info['name']}")
            
            return author_info
            
        except Exception as e:
            logger.error(f"Error fetching author {author_id}: {e}")
            raise Exception(f"Failed to fetch author: {str(e)}")
    
    def _parse_work(self, data: Dict[str, Any]) -> Work:
        """Parse OpenAlex work data into Work model"""
        # Parse authors
        authors = []
        institutions = []
        for authorship in data.get("authorships", []):
            if authorship.get("author"):
                author = Author(
                    id=authorship["author"].get("id") or None,
                    name=authorship["author"].get("display_name") or "Unknown",
                    orcid=authorship["author"].get("orcid")
                )
                authors.append(author)
            
            # Parse institutions
            for inst in authorship.get("institutions", []):
                institution = Institution(
                    id=inst.get("id") or None,
                    name=inst.get("display_name") or "Unknown",
                    country=inst.get("country_code"),
                    type=inst.get("type")
                )
                if institution not in institutions:
                    institutions.append(institution)
        
        # Parse concepts
        concepts = []
        for concept in data.get("concepts", []):
            concepts.append(Concept(
                id=concept.get("id") or None,
                display_name=concept.get("display_name") or "Unknown",
                level=concept.get("level", 0),
                score=concept.get("score", 0.0)
            ))
        
        # Parse open access
        oa_data = data.get("open_access", {})
        open_access = OpenAccess(
            is_oa=oa_data.get("is_oa", False),
            oa_status=oa_data.get("oa_status"),
            oa_url=oa_data.get("oa_url")
        )
        
        # Parse abstract
        abstract = None
        abstract_inverted = data.get("abstract_inverted_index")
        if abstract_inverted:
            # Reconstruct abstract from inverted index
            try:
                word_positions = []
                for word, positions in abstract_inverted.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join([word for _, word in word_positions])
            except Exception as e:
                logger.warning(f"Failed to reconstruct abstract: {e}")
        
        # Get primary location (venue)
        venue = None
        venue_issn = None
        primary_location = data.get("primary_location", {})
        if primary_location and primary_location.get("source"):
            venue = primary_location["source"].get("display_name")
            issn_list = primary_location["source"].get("issn_l")
            if issn_list:
                venue_issn = issn_list[0] if isinstance(issn_list, list) else issn_list
        
        # Build work object
        work = Work(
            id=data.get("id") or None,
            title=data.get("title") or "Untitled",
            publication_year=data.get("publication_year"),
            publication_date=data.get("publication_date"),
            doi=data.get("doi"),
            abstract=abstract,
            abstract_inverted_index=abstract_inverted,
            cited_by_count=data.get("cited_by_count", 0),
            authors=authors,
            institutions=institutions,
            concepts=concepts,
            open_access=open_access,
            pdf_url=open_access.oa_url if open_access.is_oa else None,
            type=data.get("type"),
            venue=venue,
            venue_issn=venue_issn,
            language=data.get("language"),
            openalex_url=data.get("id"),
            doi_url=f"https://doi.org/{data.get('doi')}" if data.get("doi") else None
        )
        
        return work

