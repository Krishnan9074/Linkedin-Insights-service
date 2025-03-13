from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from typing import List, Optional
from datetime import datetime
from app.models import (
    PostInDB, PostResponse, PostQuery, CommentResponse, PaginatedResponse
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

@router.get("", response_model=List[PostResponse])
async def list_posts(
    page_id: str = Query(..., description="LinkedIn page ID (from URL)"),
    post_type: Optional[str] = Query(None, description="Filter by post type"),
    min_reactions: Optional[int] = Query(None, description="Minimum total reactions"),
    from_date: Optional[datetime] = Query(None, description="Filter from date (ISO format)"),
    to_date: Optional[datetime] = Query(None, description="Filter to date (ISO format)"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    List LinkedIn posts for a specific page
    
    - **page_id**: The LinkedIn page ID from the URL (required)
    - **post_type**: Filter by post type (e.g., 'text', 'image', 'video')
    - **min_reactions**: Minimum total reactions count
    - **from_date**: Filter from date (ISO format)
    - **to_date**: Filter to date (ISO format)
    """
    # Check if page exists
    page = await service.get_page(page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn page with ID '{page_id}' not found"
        )
    
    posts = await service.get_posts(page_id)
    
    # Manual filtering (we can enhance the service layer to do this more efficiently)
    if post_type:
        posts = [p for p in posts if p.post_type.value == post_type]
    
    if min_reactions is not None:
        posts = [p for p in posts if p.reactions.total_count >= min_reactions]
    
    if from_date:
        posts = [p for p in posts if p.published_at and p.published_at >= from_date]
    
    if to_date:
        posts = [p for p in posts if p.published_at and p.published_at <= to_date]
    
    return posts

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str = Path(..., description="LinkedIn post ID"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    Get LinkedIn post by ID
    
    - **post_id**: The LinkedIn post ID
    """
    # This is a simple implementation that doesn't efficiently query by post_id
    # In a real implementation, you would add a dedicated method to the service layer
    
    # Get database from the service
    db = service.db
    
    post_data = await db.posts.find_one({"post_id": post_id})
    if not post_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn post with ID '{post_id}' not found"
        )
    
    return PostInDB(**post_data)

@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: str = Path(..., description="LinkedIn post ID"),
    force_scrape: bool = Query(False, description="Force scrape from LinkedIn even if in DB"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    Get comments for a LinkedIn post
    
    - **post_id**: The LinkedIn post ID
    - **force_scrape**: If true, will scrape from LinkedIn even if already in DB
    """
    # Get database from the service
    db = service.db
    
    # Check if post exists
    post_data = await db.posts.find_one({"post_id": post_id})
    if not post_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn post with ID '{post_id}' not found"
        )
    
    comments = await service.get_post_comments(post_id, force_scrape)
    return comments 