from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class Industry(str, Enum):
    """Enum for common LinkedIn industries"""
    TECHNOLOGY = "Technology"
    FINANCE = "Finance"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    RETAIL = "Retail"
    MANUFACTURING = "Manufacturing"
    CONSULTING = "Consulting"
    MEDIA = "Media"
    MARKETING = "Marketing"
    OTHER = "Other"

class PageBase(BaseModel):
    """Base model for LinkedIn Page"""
    page_id: str
    url: HttpUrl
    
class PageCreate(PageBase):
    """Model for creating a LinkedIn Page in DB"""
    name: str
    profile_picture_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    website: Optional[HttpUrl] = None
    industry: Optional[Industry] = None
    follower_count: Optional[int] = None
    head_count: Optional[int] = None
    specialities: Optional[List[str]] = Field(default_factory=list)
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    last_scraped: datetime = Field(default_factory=datetime.utcnow)

class PageInDB(PageCreate):
    """Model representing a LinkedIn Page in DB"""
    linkedin_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True

class PageResponse(PageInDB):
    """Response model for LinkedIn Page"""
    pass

class PageQuery(BaseModel):
    """Query parameters for filtering Pages"""
    name: Optional[str] = None
    industry: Optional[Industry] = None
    min_followers: Optional[int] = None
    max_followers: Optional[int] = None
    page: int = 1
    limit: int = 10
    
    class Config:
        extra = "ignore" 