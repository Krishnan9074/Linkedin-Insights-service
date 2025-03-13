from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from typing import List, Optional
from app.models import (
    UserInDB, UserResponse, UserQuery, PaginatedResponse
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

@router.get("", response_model=List[UserResponse])
async def list_employees(
    company_page_id: str = Query(..., description="LinkedIn page ID (from URL)"),
    name: Optional[str] = Query(None, description="Filter by employee name (partial match)"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    List employees for a LinkedIn page
    
    - **company_page_id**: The LinkedIn page ID (required)
    - **name**: Filter by employee name (partial match)
    """
    # Check if page exists
    page = await service.get_page(company_page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn page with ID '{company_page_id}' not found"
        )
    
    employees = await service.get_employees(company_page_id)
    
    # Manual filtering by name
    if name:
        employees = [e for e in employees if name.lower() in e.name.lower()]
    
    return employees

@router.get("/{user_id}", response_model=UserResponse)
async def get_employee(
    user_id: str = Path(..., description="LinkedIn user ID"),
    service: LinkedInService = Depends(get_linkedin_service)
):
    """
    Get LinkedIn employee by user ID
    
    - **user_id**: The LinkedIn user ID
    """
    # Get database from the service
    db = service.db
    
    user_data = await db.users.find_one({"user_id": user_id})
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn user with ID '{user_id}' not found"
        )
    
    return UserInDB(**user_data) 