from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from app.models import AISummary
from app.services.linkedin_service import LinkedInService
from app.services.ai_service import AIService
from app.core.config import settings

router = APIRouter()

async def get_linkedin_service() -> LinkedInService:
    """Dependency for getting LinkedInService instance"""
    service = LinkedInService()
    try:
        yield service
    finally:
        await service.close()

@router.get("/summary/{page_id}", response_model=AISummary)
async def get_page_ai_summary(
    page_id: str = Path(..., description="LinkedIn page ID (from URL)"),
    force_generate: bool = Query(False, description="Force regenerate AI summary"),
    linkedin_service: LinkedInService = Depends(get_linkedin_service)
):
    """
    Get Gemini AI-generated summary for a LinkedIn page
    
    - **page_id**: The LinkedIn page ID from the URL
    - **force_generate**: If true, will regenerate summary even if already cached
    """
    # Check if Gemini API key is configured
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini AI API key not configured. Please set GEMINI_API_KEY in environment variables."
        )
    
    # Get database from the service
    db = linkedin_service.db
    
    # Check cache first unless force_generate is True
    if not force_generate:
        summary_data = await db.ai_summaries.find_one({"page_id": page_id})
        if summary_data:
            return AISummary(**summary_data)
    
    # Get page data
    page = await linkedin_service.get_page(page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LinkedIn page with ID '{page_id}' not found"
        )
    
    # Get posts and employees
    posts = await linkedin_service.get_posts(page_id)
    employees = await linkedin_service.get_employees(page_id)
    
    # Generate AI summary
    ai_service = AIService()
    summary = await ai_service.generate_page_summary(page, posts, employees)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Gemini AI summary"
        )
    
    # Save to database
    await db.ai_summaries.update_one(
        {"page_id": page_id},
        {"$set": summary.dict()},
        upsert=True
    )
    
    return summary 