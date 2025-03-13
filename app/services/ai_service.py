import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import google.generativeai as genai
from app.core.config import settings
from app.models import AISummary, PageInDB, PostInDB, UserInDB

logger = logging.getLogger(__name__)

class AIService:
    """Service for generating AI-based insights and summaries using Google's Gemini"""
    
    def __init__(self):
        """Initialize AIService with Gemini configuration"""
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
    async def generate_page_summary(
        self, 
        page: PageInDB, 
        posts: List[PostInDB], 
        employees: List[UserInDB]
    ) -> Optional[AISummary]:
        """Generate AI summary for LinkedIn page using Gemini"""
        try:
            if not settings.GEMINI_API_KEY:
                logger.error("Gemini API key not provided")
                return None
                
            # Prepare data for the prompt
            page_data = {
                "name": page.name,
                "description": page.description,
                "industry": page.industry.value if page.industry else "Unknown",
                "follower_count": page.follower_count,
                "head_count": page.head_count,
                "specialities": page.specialities
            }
            
            # Get top 5 posts for analysis
            top_posts = posts[:5] if posts else []
            posts_data = []
            for post in top_posts:
                posts_data.append({
                    "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                    "reactions": post.reactions.total_count,
                    "type": post.post_type.value
                })
            
            # Get employee data
            employee_data = []
            for employee in employees[:10]:  # Limit to 10 employees
                employee_data.append({
                    "headline": employee.headline,
                    "location": employee.location
                })
            
            # Construct the prompt
            prompt = f"""
            You are an expert business analyst. Analyze this LinkedIn page data and provide a concise summary.
            
            Page information:
            - Name: {page_data['name']}
            - Industry: {page_data['industry']}
            - Follower count: {page_data['follower_count']}
            - Employee count: {page_data['head_count']}
            - Specialities: {', '.join(page_data['specialities']) if page_data['specialities'] else 'None specified'}
            
            Description:
            {page_data['description']}
            
            Recent Posts ({len(posts_data)}):
            {json.dumps(posts_data, indent=2)}
            
            Employee sample ({len(employee_data)}):
            {json.dumps(employee_data, indent=2)}
            
            Based on this information, provide:
            1. A concise summary of the company (3-4 sentences)
            2. Follower insights: Analysis of their follower count compared to industry standards
            3. Engagement insights: Analysis of their post engagement levels
            4. Content insights: What types of content seem to perform best for them
            
            Format your response as JSON with these fields: summary, follower_insights, engagement_insights, content_insights
            """
            
            # Call Gemini API
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = model.generate_content(prompt)
            
            # Parse JSON response
            try:
                # Extract JSON from the response
                ai_response = response.text
                ai_data = json.loads(ai_response)
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Error parsing Gemini response: {e}")
                # If Gemini didn't return valid JSON, create a basic response
                ai_data = {
                    "summary": "Generated summary contained formatting errors.",
                    "follower_insights": None,
                    "engagement_insights": None,
                    "content_insights": None
                }
            
            # Create AI summary object
            ai_summary = AISummary(
                page_id=page.page_id,
                summary=ai_data.get("summary", "No summary generated."),
                follower_insights=ai_data.get("follower_insights"),
                engagement_insights=ai_data.get("engagement_insights"),
                content_insights=ai_data.get("content_insights"),
                created_at=datetime.utcnow().isoformat(),
                extra_data={}
            )
            
            return ai_summary
        except Exception as e:
            logger.error(f"Error generating AI summary with Gemini: {e}")
            return None 