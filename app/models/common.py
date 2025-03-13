from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional, Any, Dict
from enum import Enum

T = TypeVar('T')

class SortOrder(str, Enum):
    """Sort order enum"""
    ASC = "asc"
    DESC = "desc"

class PageParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    limit: int = 10
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, page_params: PageParams) -> "PaginatedResponse[T]":
        """Create paginated response"""
        pages = (total + page_params.limit - 1) // page_params.limit if page_params.limit > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page_params.page,
            limit=page_params.limit,
            pages=pages
        )

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str
    
class StatusResponse(BaseModel):
    """Status response model"""
    status: str
    message: str
    
class AISummary(BaseModel):
    """AI Summary model for LinkedIn Page"""
    page_id: str
    summary: str
    follower_insights: Optional[str] = None
    engagement_insights: Optional[str] = None
    content_insights: Optional[str] = None
    created_at: str = Field(...)
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict) 