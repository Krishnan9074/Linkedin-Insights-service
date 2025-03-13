from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    """Base model for LinkedIn User"""
    user_id: str
    url: HttpUrl

class UserCreate(UserBase):
    """Model for creating a LinkedIn User in DB"""
    name: str
    profile_picture_url: Optional[HttpUrl] = None
    headline: Optional[str] = None
    company: Optional[str] = None
    company_page_id: Optional[str] = None
    location: Optional[str] = None
    connection_count: Optional[int] = None
    follower_count: Optional[int] = None
    is_employee: bool = False
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    last_scraped: datetime = Field(default_factory=datetime.utcnow)

class UserInDB(UserCreate):
    """Model representing a LinkedIn User in DB"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True

class UserResponse(UserInDB):
    """Response model for LinkedIn User"""
    pass

class UserQuery(BaseModel):
    """Query parameters for filtering Users"""
    company_page_id: Optional[str] = None
    is_employee: Optional[bool] = None
    name: Optional[str] = None
    page: int = 1
    limit: int = 10
    
    class Config:
        extra = "ignore" 