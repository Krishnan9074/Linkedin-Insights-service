from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime

class CommentBase(BaseModel):
    """Base model for LinkedIn Comment"""
    comment_id: str
    post_id: str
    user_id: str

class CommentCreate(CommentBase):
    """Model for creating a LinkedIn Comment in DB"""
    content: str
    like_count: int = 0
    reply_count: int = 0
    parent_comment_id: Optional[str] = None
    published_at: Optional[datetime] = None
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    last_scraped: datetime = Field(default_factory=datetime.utcnow)

class CommentInDB(CommentCreate):
    """Model representing a LinkedIn Comment in DB"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True

class CommentResponse(CommentInDB):
    """Response model for LinkedIn Comment"""
    pass

class CommentQuery(BaseModel):
    """Query parameters for filtering Comments"""
    post_id: Optional[str] = None
    user_id: Optional[str] = None
    parent_comment_id: Optional[str] = None
    page: int = 1
    limit: int = 10
    
    class Config:
        extra = "ignore" 