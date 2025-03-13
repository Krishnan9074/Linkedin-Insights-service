from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from typing import List, Optional
from app.models import (
    CommentInDB, CommentResponse, CommentQuery, PaginatedResponse
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

@router.get("", response_model=List[CommentResponse])
async def list_comments(
    post_id: str = Query(..., description="LinkedIn post ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    parent_comment_id: Optional[str] = Query(None, description="Filter by parent comment ID for replies"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    List comments for a LinkedIn post
    
    - **post_id**: The LinkedIn post ID (required)
    - **user_id**: Filter by user ID
    - **parent_comment_id**: Filter by parent comment ID (for replies)
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
    
    comments = await service.get_post_comments(post_id)
    
    # Manual filtering
    if user_id:
        comments = [c for c in comments if c.user_id == user_id]
    
    if parent_comment_id:
        comments = [c for c in comments if c.parent_comment_id == parent_comment_id]
    
    return comments

@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: str = Path(..., description="LinkedIn comment ID"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    Get LinkedIn comment by ID
    
    - **comment_id**: The LinkedIn comment ID
    """
    # Get database from the service
    db = service.db
    
    comment_data = await db.comments.find_one({"comment_id": comment_id})
    if not comment_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn comment with ID '{comment_id}' not found"
        )
    
    return CommentInDB(**comment_data) 