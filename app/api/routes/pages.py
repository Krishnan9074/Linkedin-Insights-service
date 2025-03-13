from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from typing import List, Optional
from app.models import (
    PageInDB, PageResponse, PageQuery, PostResponse, 
    UserResponse, PaginatedResponse
)
from app.services.linkedin_service import LinkedInService

router = APIRouter()

async def get_linkedin_service() -> LinkedInService:
    """Dependency for getting LinkedInService instance"""
    service = LinkedInService()
    try:
        yield service
    finally:
        await service.close()

@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: str = Path(..., description="LinkedIn page ID (from URL, e.g. 'deepsolv')"),
    force_scrape: bool = Query(False, description="Force scrape from LinkedIn even if in DB"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    Get LinkedIn page details by page ID
    
    - **page_id**: The LinkedIn page ID from the URL (e.g., 'deepsolv' from https://www.linkedin.com/company/deepsolv/)
    - **force_scrape**: If true, will scrape from LinkedIn even if already in DB
    """
    page = await service.get_page(page_id, force_scrape)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn page with ID '{page_id}' not found"
        )
    return page

@router.get("", response_model=PaginatedResponse[PageResponse])
async def list_pages(
    name: Optional[str] = Query(None, description="Filter by page name (partial match)"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    min_followers: Optional[int] = Query(None, description="Minimum follower count"),
    max_followers: Optional[int] = Query(None, description="Maximum follower count"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    List LinkedIn pages with filtering options
    
    - **name**: Filter by page name (partial match)
    - **industry**: Filter by industry (e.g., 'Technology', 'Finance')
    - **min_followers**: Minimum follower count
    - **max_followers**: Maximum follower count
    - **page**: Page number (starting from 1)
    - **limit**: Number of items per page (max 100)
    """
    query = PageQuery(
        name=name,
        industry=industry,
        min_followers=min_followers,
        max_followers=max_followers,
        page=page,
        limit=limit
    )
    pages = await service.query_pages(query)
    return pages

@router.get("/{page_id}/posts", response_model=List[PostResponse])
async def get_page_posts(
    page_id: str = Path(..., description="LinkedIn page ID (from URL)"),
    force_scrape: bool = Query(False, description="Force scrape from LinkedIn even if in DB"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    Get posts from a LinkedIn page
    
    - **page_id**: The LinkedIn page ID from the URL
    - **force_scrape**: If true, will scrape from LinkedIn even if already in DB
    """
    # First check if page exists
    page = await service.get_page(page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn page with ID '{page_id}' not found"
        )
    
    posts = await service.get_posts(page_id, force_scrape)
    return posts

@router.get("/{page_id}/employees", response_model=List[UserResponse])
async def get_page_employees(
    page_id: str = Path(..., description="LinkedIn page ID (from URL)"),
    force_scrape: bool = Query(False, description="Force scrape from LinkedIn even if in DB"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    Get employees from a LinkedIn page
    
    - **page_id**: The LinkedIn page ID from the URL
    - **force_scrape**: If true, will scrape from LinkedIn even if already in DB
    """
    # First check if page exists
    page = await service.get_page(page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn page with ID '{page_id}' not found"
        )
    
    employees = await service.get_employees(page_id, force_scrape)
    return employees

@router.post("/{page_id}/scrape", response_model=PageResponse, status_code=status.HTTP_200_OK)
async def scrape_page_data(
    page_id: str = Path(..., description="LinkedIn page ID (from URL)"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    Scrape all data for a LinkedIn page (page details, posts, employees, comments)
    
    - **page_id**: The LinkedIn page ID from the URL
    """
    page, _, _, _ = await service.scrape_page_data(page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn page with ID '{page_id}' not found or scraping failed"
        )
    return page 