import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from app.scraper.linkedin_scraper import LinkedInScraper
from app.db.mongodb import get_database
from app.db.redis import get_cache, set_cache, delete_cache
from app.models import (
    PageCreate, PageInDB, PostCreate, PostInDB, 
    CommentCreate, CommentInDB, UserCreate, UserInDB,
    PageQuery, PostQuery, CommentQuery, UserQuery,
    PaginatedResponse, PageParams
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class LinkedInService:
    """Service for managing LinkedIn data"""
    
    def __init__(self):
        """Initialize LinkedInService"""
        self.db = get_database()
        self.scraper = None
    
    async def get_scraper(self) -> LinkedInScraper:
        """Get or create LinkedInScraper instance"""
        if not self.scraper:
            self.scraper = LinkedInScraper()
            await self.scraper.initialize()
        return self.scraper
    
    async def get_page(self, page_id: str, force_scrape: bool = False) -> Optional[PageInDB]:
        """
        Get LinkedIn page by ID
        
        If page is not in DB or force_scrape is True, it will be scraped from LinkedIn
        """
        # Try to get from cache first
        cache_key = f"page:{page_id}"
        if not force_scrape:
            cached_page = await get_cache(cache_key)
            if cached_page:
                logger.info(f"Found page {page_id} in cache")
                return PageInDB(**cached_page)
        
        # Try to get from DB
        db = get_database()
        if not force_scrape:
            page_data = await db.pages.find_one({"page_id": page_id})
            if page_data:
                logger.info(f"Found page {page_id} in database")
                page = PageInDB(**page_data)
                # Update cache
                await set_cache(cache_key, page.dict())
                return page
        
        # Scrape from LinkedIn
        logger.info(f"Scraping page {page_id} from LinkedIn")
        scraper = await self.get_scraper()
        page_create = await scraper.scrape_page(page_id)
        
        if not page_create:
            logger.error(f"Failed to scrape page {page_id}")
            return None
        
        # Save to DB
        page_dict = page_create.dict()
        page_dict["created_at"] = datetime.utcnow()
        page_dict["updated_at"] = datetime.utcnow()
        
        await db.pages.update_one(
            {"page_id": page_id},
            {"$set": page_dict},
            upsert=True
        )
        
        # Get the saved page
        page_data = await db.pages.find_one({"page_id": page_id})
        if not page_data:
            logger.error(f"Failed to save page {page_id}")
            return None
        
        page = PageInDB(**page_data)
        
        # Update cache
        await set_cache(cache_key, page.dict())
        
        return page
    
    async def get_posts(self, page_id: str, force_scrape: bool = False) -> List[PostInDB]:
        """
        Get LinkedIn page posts
        
        If posts are not in DB or force_scrape is True, they will be scraped from LinkedIn
        """
        # Try to get from cache first
        cache_key = f"posts:{page_id}"
        if not force_scrape:
            cached_posts = await get_cache(cache_key)
            if cached_posts:
                logger.info(f"Found posts for page {page_id} in cache")
                return [PostInDB(**post) for post in cached_posts]
        
        # Try to get from DB
        db = get_database()
        if not force_scrape:
            posts_data = await db.posts.find({"page_id": page_id}).sort("published_at", -1).limit(settings.MAX_POSTS_TO_SCRAPE).to_list(length=settings.MAX_POSTS_TO_SCRAPE)
            if posts_data and len(posts_data) > 0:
                logger.info(f"Found {len(posts_data)} posts for page {page_id} in database")
                posts = [PostInDB(**post) for post in posts_data]
                # Update cache
                await set_cache(cache_key, [post.dict() for post in posts])
                return posts
        
        # Scrape from LinkedIn
        logger.info(f"Scraping posts for page {page_id} from LinkedIn")
        scraper = await self.get_scraper()
        posts_create = await scraper.scrape_posts(page_id)
        
        if not posts_create or len(posts_create) == 0:
            logger.warning(f"No posts found for page {page_id}")
            return []
        
        # Save to DB
        for post_create in posts_create:
            post_dict = post_create.dict()
            post_dict["created_at"] = datetime.utcnow()
            post_dict["updated_at"] = datetime.utcnow()
            
            await db.posts.update_one(
                {"post_id": post_dict["post_id"]},
                {"$set": post_dict},
                upsert=True
            )
        
        # Get the saved posts
        posts_data = await db.posts.find({"page_id": page_id}).sort("published_at", -1).limit(settings.MAX_POSTS_TO_SCRAPE).to_list(length=settings.MAX_POSTS_TO_SCRAPE)
        posts = [PostInDB(**post) for post in posts_data]
        
        # Update cache
        await set_cache(cache_key, [post.dict() for post in posts])
        
        return posts
    
    async def get_employees(self, page_id: str, force_scrape: bool = False) -> List[UserInDB]:
        """
        Get LinkedIn page employees
        
        If employees are not in DB or force_scrape is True, they will be scraped from LinkedIn
        """
        # Try to get from cache first
        cache_key = f"employees:{page_id}"
        if not force_scrape:
            cached_employees = await get_cache(cache_key)
            if cached_employees:
                logger.info(f"Found employees for page {page_id} in cache")
                return [UserInDB(**user) for user in cached_employees]
        
        # Try to get from DB
        db = get_database()
        if not force_scrape:
            employees_data = await db.users.find({"company_page_id": page_id, "is_employee": True}).to_list(length=100)
            if employees_data and len(employees_data) > 0:
                logger.info(f"Found {len(employees_data)} employees for page {page_id} in database")
                employees = [UserInDB(**user) for user in employees_data]
                # Update cache
                await set_cache(cache_key, [employee.dict() for employee in employees])
                return employees
        
        # Scrape from LinkedIn
        logger.info(f"Scraping employees for page {page_id} from LinkedIn")
        scraper = await self.get_scraper()
        employees_create = await scraper.scrape_employees(page_id)
        
        if not employees_create or len(employees_create) == 0:
            logger.warning(f"No employees found for page {page_id}")
            return []
        
        # Save to DB
        for employee_create in employees_create:
            employee_dict = employee_create.dict()
            employee_dict["created_at"] = datetime.utcnow()
            employee_dict["updated_at"] = datetime.utcnow()
            
            await db.users.update_one(
                {"user_id": employee_dict["user_id"]},
                {"$set": employee_dict},
                upsert=True
            )
        
        # Get the saved employees
        employees_data = await db.users.find({"company_page_id": page_id, "is_employee": True}).to_list(length=100)
        employees = [UserInDB(**user) for user in employees_data]
        
        # Update cache
        await set_cache(cache_key, [employee.dict() for employee in employees])
        
        return employees
    
    async def get_post_comments(self, post_id: str, force_scrape: bool = False) -> List[CommentInDB]:
        """
        Get LinkedIn post comments
        
        If comments are not in DB or force_scrape is True, they will be scraped from LinkedIn
        """
        # Try to get from cache first
        cache_key = f"comments:{post_id}"
        if not force_scrape:
            cached_comments = await get_cache(cache_key)
            if cached_comments:
                logger.info(f"Found comments for post {post_id} in cache")
                return [CommentInDB(**comment) for comment in cached_comments]
        
        # Try to get from DB
        db = get_database()
        if not force_scrape:
            comments_data = await db.comments.find({"post_id": post_id}).to_list(length=100)
            if comments_data and len(comments_data) > 0:
                logger.info(f"Found {len(comments_data)} comments for post {post_id} in database")
                comments = [CommentInDB(**comment) for comment in comments_data]
                # Update cache
                await set_cache(cache_key, [comment.dict() for comment in comments])
                return comments
        
        # Scrape from LinkedIn
        logger.info(f"Scraping comments for post {post_id} from LinkedIn")
        
        # First, get the post to get its URL
        post_data = await db.posts.find_one({"post_id": post_id})
        if not post_data:
            logger.error(f"Post {post_id} not found in database")
            return []
        
        post = PostInDB(**post_data)
        
        scraper = await self.get_scraper()
        comments_create = await scraper.scrape_comments(post_id, str(post.url))
        
        if not comments_create or len(comments_create) == 0:
            logger.warning(f"No comments found for post {post_id}")
            return []
        
        # Save to DB
        for comment_create in comments_create:
            comment_dict = comment_create.dict()
            comment_dict["created_at"] = datetime.utcnow()
            comment_dict["updated_at"] = datetime.utcnow()
            
            await db.comments.update_one(
                {"comment_id": comment_dict["comment_id"]},
                {"$set": comment_dict},
                upsert=True
            )
        
        # Get the saved comments
        comments_data = await db.comments.find({"post_id": post_id}).to_list(length=100)
        comments = [CommentInDB(**comment) for comment in comments_data]
        
        # Update cache
        await set_cache(cache_key, [comment.dict() for comment in comments])
        
        return comments
    
    async def scrape_page_data(self, page_id: str) -> Tuple[Optional[PageInDB], List[PostInDB], List[UserInDB], List[CommentInDB]]:
        """
        Scrape and save all data for a LinkedIn page
        """
        logger.info(f"Scraping all data for page {page_id}")
        
        scraper = await self.get_scraper()
        page_create, posts_create, employees_create, comments_create = await scraper.scrape_all(page_id)
        
        if not page_create:
            logger.error(f"Failed to scrape page {page_id}")
            return None, [], [], []
        
        db = get_database()
        
        # Save page
        page_dict = page_create.dict()
        page_dict["created_at"] = datetime.utcnow()
        page_dict["updated_at"] = datetime.utcnow()
        
        await db.pages.update_one(
            {"page_id": page_id},
            {"$set": page_dict},
            upsert=True
        )
        
        # Save posts
        saved_posts = []
        for post_create in posts_create:
            post_dict = post_create.dict()
            post_dict["created_at"] = datetime.utcnow()
            post_dict["updated_at"] = datetime.utcnow()
            
            await db.posts.update_one(
                {"post_id": post_dict["post_id"]},
                {"$set": post_dict},
                upsert=True
            )
            
            post_data = await db.posts.find_one({"post_id": post_dict["post_id"]})
            if post_data:
                saved_posts.append(PostInDB(**post_data))
        
        # Save employees
        saved_employees = []
        for employee_create in employees_create:
            employee_dict = employee_create.dict()
            employee_dict["created_at"] = datetime.utcnow()
            employee_dict["updated_at"] = datetime.utcnow()
            
            await db.users.update_one(
                {"user_id": employee_dict["user_id"]},
                {"$set": employee_dict},
                upsert=True
            )
            
            user_data = await db.users.find_one({"user_id": employee_dict["user_id"]})
            if user_data:
                saved_employees.append(UserInDB(**user_data))
        
        # Save comments
        saved_comments = []
        for comment_create in comments_create:
            comment_dict = comment_create.dict()
            comment_dict["created_at"] = datetime.utcnow()
            comment_dict["updated_at"] = datetime.utcnow()
            
            await db.comments.update_one(
                {"comment_id": comment_dict["comment_id"]},
                {"$set": comment_dict},
                upsert=True
            )
            
            comment_data = await db.comments.find_one({"comment_id": comment_dict["comment_id"]})
            if comment_data:
                saved_comments.append(CommentInDB(**comment_data))
        
        # Get the saved page
        page_data = await db.pages.find_one({"page_id": page_id})
        if not page_data:
            logger.error(f"Failed to save page {page_id}")
            return None, saved_posts, saved_employees, saved_comments
        
        page = PageInDB(**page_data)
        
        # Update caches
        await set_cache(f"page:{page_id}", page.dict())
        await set_cache(f"posts:{page_id}", [post.dict() for post in saved_posts])
        await set_cache(f"employees:{page_id}", [employee.dict() for employee in saved_employees])
        
        # Update post comment caches
        for post in saved_posts:
            post_comments = [c for c in saved_comments if c.post_id == post.post_id]
            if post_comments:
                await set_cache(f"comments:{post.post_id}", [comment.dict() for comment in post_comments])
        
        return page, saved_posts, saved_employees, saved_comments
    
    async def query_pages(self, query: PageQuery) -> PaginatedResponse:
        """
        Query LinkedIn pages with filters
        """
        db = get_database()
        
        # Build query
        mongo_query = {}
        
        if query.name:
            mongo_query["$text"] = {"$search": query.name}
        
        if query.industry:
            mongo_query["industry"] = query.industry.value
        
        if query.min_followers is not None:
            mongo_query["follower_count"] = mongo_query.get("follower_count", {})
            mongo_query["follower_count"]["$gte"] = query.min_followers
        
        if query.max_followers is not None:
            mongo_query["follower_count"] = mongo_query.get("follower_count", {})
            mongo_query["follower_count"]["$lte"] = query.max_followers
        
        # Pagination params
        page_params = PageParams(page=query.page, limit=min(query.limit, settings.MAX_PAGE_SIZE))
        
        # Get total count
        total = await db.pages.count_documents(mongo_query)
        
        # Get pages
        pages_data = await db.pages.find(mongo_query).skip(page_params.skip).limit(page_params.limit).to_list(length=page_params.limit)
        
        # Convert to model
        pages = [PageInDB(**page) for page in pages_data]
        
        return PaginatedResponse.create(items=pages, total=total, page_params=page_params)
    
    async def close(self):
        """Close scraper"""
        if self.scraper:
            await self.scraper.close() 