from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class PostType(str, Enum):
    """Enum for LinkedIn post types"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    ARTICLE = "article"
    DOCUMENT = "document"
    POLL = "poll"
    OTHER = "other"

class Reactions(BaseModel):
    """LinkedIn post reactions"""
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    total_count: int = 0

class PostBase(BaseModel):
    """Base model for LinkedIn Post"""
    post_id: str
    page_id: str
    url: HttpUrl

class PostCreate(PostBase):
    """Model for creating a LinkedIn Post in DB"""
    post_type: PostType = PostType.TEXT
    content: str
    media_urls: Optional[List[HttpUrl]] = Field(default_factory=list)
    reactions: Reactions = Field(default_factory=Reactions)
    published_at: Optional[datetime] = None
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    last_scraped: datetime = Field(default_factory=datetime.utcnow)

class PostInDB(PostCreate):
    """Model representing a LinkedIn Post in DB"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True

class PostResponse(PostInDB):
    """Response model for LinkedIn Post"""
    pass

class PostQuery(BaseModel):
    """Query parameters for filtering Posts"""
    page_id: Optional[str] = None
    post_type: Optional[PostType] = None
    min_reactions: Optional[int] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = 1
    limit: int = 10
    
    class Config:
        extra = "ignore" 