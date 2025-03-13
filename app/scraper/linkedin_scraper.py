import asyncio
import logging
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from app.core.config import settings
from app.models import (
    PageCreate, PostCreate, UserCreate, CommentCreate, 
    PostType, Reactions, Industry
)

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """LinkedIn scraper class for extracting page details, posts, comments and employees"""
    
    def __init__(self, headless: bool = True):
        """Initialize LinkedInScraper"""
        self.headless = headless
        self.driver = None
        self.base_url = settings.LINKEDIN_BASE_URL
        self.max_posts = settings.MAX_POSTS_TO_SCRAPE
        self.is_logged_in = False
    
    async def initialize(self) -> None:
        """Initialize and set up the WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Initialized WebDriver")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    async def login(self) -> bool:
        """Login to LinkedIn"""
        if not settings.LINKEDIN_EMAIL or not settings.LINKEDIN_PASSWORD:
            logger.warning("LinkedIn credentials not provided, proceeding without login")
            return False
        
        try:
            self.driver.get(f"{self.base_url}/login")
            
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_input.send_keys(settings.LINKEDIN_EMAIL)
            
            password_input = self.driver.find_element(By.ID, "password")
            password_input.send_keys(settings.LINKEDIN_PASSWORD)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("feed")
            )
            
            logger.info("Successfully logged in to LinkedIn")
            self.is_logged_in = True
            return True
        except Exception as e:
            logger.error(f"Failed to login to LinkedIn: {e}")
            return False
    
    async def close(self) -> None:
        """Close WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("Closed WebDriver")
    
    async def scrape_page(self, page_id: str) -> Optional[PageCreate]:
        """Scrape LinkedIn page details"""
        if not self.driver:
            await self.initialize()
        
        page_url = f"{self.base_url}/company/{page_id}"
        try:
            self.driver.get(page_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".org-top-card"))
            )
            
            # Get page HTML
            page_html = self.driver.page_source
            soup = BeautifulSoup(page_html, "html.parser")
            
            # Extract page details
            page_data = await self._extract_page_data(soup, page_id, page_url)
            if not page_data:
                logger.error(f"Failed to extract data for page: {page_id}")
                return None
            
            return PageCreate(**page_data)
        except Exception as e:
            logger.error(f"Error scraping page {page_id}: {e}")
            return None
    
    async def _extract_page_data(self, soup: BeautifulSoup, page_id: str, page_url: str) -> Dict[str, Any]:
        """Extract page data from BeautifulSoup object"""
        try:
            # Basic page info
            top_card = soup.select_one(".org-top-card")
            if not top_card:
                logger.error("Could not find top card section")
                return {}
            
            name = top_card.select_one(".org-top-card__title")
            name = name.get_text().strip() if name else ""
            
            profile_picture = top_card.select_one(".org-top-card__logo-img")
            profile_picture_url = profile_picture.get("src") if profile_picture else None
            
            # Follower count
            follower_count_elem = soup.select_one(".org-top-card-secondary-content__connections")
            follower_count = 0
            if follower_count_elem:
                follower_text = follower_count_elem.get_text().strip()
                # Extract numbers from text like "123,456 followers"
                follower_match = re.search(r'([\d,]+)', follower_text)
                if follower_match:
                    follower_count = int(follower_match.group(1).replace(',', ''))
            
            # About section
            about_section = soup.select_one(".org-about-module__description")
            description = about_section.get_text().strip() if about_section else ""
            
            # Website
            website_elem = soup.select_one("a.link-without-visited-state[href*='http']")
            website = website_elem.get("href") if website_elem else None
            
            # Industry
            industry_elem = soup.select_one(".org-about-module__industry")
            industry_text = industry_elem.get_text().strip() if industry_elem else "Other"
            try:
                industry = Industry(industry_text)
            except ValueError:
                industry = Industry.OTHER
            
            # Head count
            headcount_elem = soup.select_one(".org-about-module__company-staff-count-range")
            head_count = 0
            if headcount_elem:
                headcount_text = headcount_elem.get_text().strip()
                # Extract the first number from ranges like "1,001-5,000 employees"
                headcount_match = re.search(r'([\d,]+)', headcount_text)
                if headcount_match:
                    head_count = int(headcount_match.group(1).replace(',', ''))
            
            # Specialities
            specialities_elem = soup.select_one(".org-about-module__specialities")
            specialities = []
            if specialities_elem:
                specialities_text = specialities_elem.get_text().strip()
                if "Specialties" in specialities_text:
                    specialities_parts = specialities_text.split("Specialties")
                    if len(specialities_parts) > 1:
                        specialities = [s.strip() for s in specialities_parts[1].split(",")]
            
            # LinkedIn ID from page HTML
            linkedin_id = ""
            page_script = soup.select_one("script[type='application/ld+json']")
            if page_script:
                try:
                    script_data = json.loads(page_script.string)
                    linkedin_id = script_data.get("@id", "").split(":")[-1]
                except (json.JSONDecodeError, IndexError, AttributeError):
                    pass
            
            # Construct the page data
            page_data = {
                "page_id": page_id,
                "url": page_url,
                "name": name,
                "profile_picture_url": profile_picture_url,
                "description": description,
                "website": website,
                "industry": industry,
                "follower_count": follower_count,
                "head_count": head_count,
                "specialities": specialities,
                "extra_data": {
                    "linkedin_id": linkedin_id
                },
                "last_scraped": datetime.utcnow()
            }
            
            return page_data
        except Exception as e:
            logger.error(f"Error extracting page data: {e}")
            return {}
    
    async def scrape_posts(self, page_id: str) -> List[PostCreate]:
        """Scrape LinkedIn page posts"""
        if not self.driver:
            await self.initialize()
        
        posts_url = f"{self.base_url}/company/{page_id}/posts"
        posts = []
        
        try:
            self.driver.get(posts_url)
            
            # Wait for posts to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".org-updates__content"))
            )
            
            # Scroll to load more posts
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while len(posts) < self.max_posts:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for content to load
                time.sleep(2)
                
                # Check if we've scrolled to the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                
                last_height = new_height
                
                # Get page HTML and extract posts
                post_html = self.driver.page_source
                soup = BeautifulSoup(post_html, "html.parser")
                
                post_elements = soup.select(".update-components-actor__sub-description")
                
                # Extract each post
                for post_elem in post_elements:
                    try:
                        post_container = post_elem.parent.parent.parent
                        post_data = await self._extract_post_data(post_container, page_id)
                        
                        if post_data and post_data.get("post_id"):
                            # Check if post already exists in list
                            if not any(p.post_id == post_data["post_id"] for p in posts):
                                posts.append(PostCreate(**post_data))
                                
                                if len(posts) >= self.max_posts:
                                    break
                    except Exception as e:
                        logger.error(f"Error extracting post: {e}")
            
            logger.info(f"Scraped {len(posts)} posts for page {page_id}")
            return posts
        except Exception as e:
            logger.error(f"Error scraping posts for page {page_id}: {e}")
            return []
    
    async def _extract_post_data(self, post_element: Any, page_id: str) -> Dict[str, Any]:
        """Extract post data from post element"""
        try:
            # Post ID
            post_link = post_element.select_one("a.app-aware-link")
            post_url = post_link.get("href") if post_link else ""
            post_id = post_url.split("/")[-1] if post_url and "/posts/" in post_url else ""
            
            if not post_id:
                return {}
            
            # Post content
            content_elem = post_element.select_one(".update-components-text")
            content = content_elem.get_text().strip() if content_elem else ""
            
            # Post type
            post_type = PostType.TEXT
            if post_element.select_one(".update-components-image"):
                post_type = PostType.IMAGE
            elif post_element.select_one(".update-components-video"):
                post_type = PostType.VIDEO
            elif post_element.select_one(".update-components-article"):
                post_type = PostType.ARTICLE
            elif post_element.select_one(".update-components-document"):
                post_type = PostType.DOCUMENT
            elif post_element.select_one(".update-components-poll"):
                post_type = PostType.POLL
            
            # Media URLs
            media_urls = []
            media_elems = post_element.select(".update-components-image__image")
            for media in media_elems:
                if media.get("src"):
                    media_urls.append(media.get("src"))
            
            # Reactions
            like_count = 0
            comment_count = 0
            share_count = 0
            
            reactions_elem = post_element.select_one(".social-details-social-counts__reactions-count")
            if reactions_elem:
                reactions_text = reactions_elem.get_text().strip()
                like_match = re.search(r'([\d,]+)', reactions_text)
                if like_match:
                    like_count = int(like_match.group(1).replace(',', ''))
            
            comments_elem = post_element.select_one(".social-details-social-counts__comments")
            if comments_elem:
                comments_text = comments_elem.get_text().strip()
                comment_match = re.search(r'([\d,]+)', comments_text)
                if comment_match:
                    comment_count = int(comment_match.group(1).replace(',', ''))
            
            # Published date (approximate)
            time_elem = post_element.select_one(".update-components-actor__sub-description")
            published_at = None
            if time_elem:
                published_text = time_elem.get_text().strip()
                # Parse relative time (very basic)
                if "hour" in published_text or "minute" in published_text:
                    published_at = datetime.utcnow()
                elif "day" in published_text:
                    days_ago = re.search(r'(\d+)', published_text)
                    if days_ago:
                        days = int(days_ago.group(1))
                        # Subtract days from current date
                        published_at = datetime.utcnow()
                elif "week" in published_text:
                    weeks_ago = re.search(r'(\d+)', published_text)
                    if weeks_ago:
                        weeks = int(weeks_ago.group(1))
                        # Subtract weeks from current date
                        published_at = datetime.utcnow()
                else:
                    published_at = datetime.utcnow()
            
            # Construct post data
            post_data = {
                "post_id": post_id,
                "page_id": page_id,
                "url": urljoin(self.base_url, post_url),
                "post_type": post_type,
                "content": content,
                "media_urls": media_urls,
                "reactions": {
                    "like_count": like_count,
                    "comment_count": comment_count,
                    "share_count": share_count,
                    "total_count": like_count + comment_count + share_count
                },
                "published_at": published_at,
                "extra_data": {},
                "last_scraped": datetime.utcnow()
            }
            
            return post_data
        except Exception as e:
            logger.error(f"Error extracting post data: {e}")
            return {}
    
    async def scrape_comments(self, post_id: str, post_url: str) -> List[CommentCreate]:
        """Scrape comments for a LinkedIn post"""
        if not self.driver:
            await self.initialize()
        
        comments = []
        
        try:
            self.driver.get(post_url)
            
            # Wait for comments to load
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".comments-comment-item"))
                )
            except:
                # No comments found
                return []
            
            # Load more comments if available
            load_more_button = self.driver.find_elements(By.CSS_SELECTOR, ".comments-comments-list__load-more-comments-button")
            if load_more_button:
                try:
                    load_more_button[0].click()
                    time.sleep(2)
                except:
                    pass
            
            # Get page HTML and extract comments
            comments_html = self.driver.page_source
            soup = BeautifulSoup(comments_html, "html.parser")
            
            comment_elements = soup.select(".comments-comment-item")
            
            # Extract each comment
            for comment_elem in comment_elements:
                try:
                    comment_data = await self._extract_comment_data(comment_elem, post_id)
                    if comment_data and comment_data.get("comment_id"):
                        comments.append(CommentCreate(**comment_data))
                except Exception as e:
                    logger.error(f"Error extracting comment: {e}")
            
            logger.info(f"Scraped {len(comments)} comments for post {post_id}")
            return comments
        except Exception as e:
            logger.error(f"Error scraping comments for post {post_id}: {e}")
            return []
    
    async def _extract_comment_data(self, comment_element: Any, post_id: str) -> Dict[str, Any]:
        """Extract comment data from comment element"""
        try:
            # Comment ID (generate from user ID and timestamp if not available)
            timestamp = datetime.utcnow().timestamp()
            comment_id = f"comment_{timestamp}"
            
            # User ID
            user_link = comment_element.select_one(".comments-post-meta__name-text")
            user_url = user_link.parent.get("href") if user_link and user_link.parent else ""
            user_id = user_url.split("/")[-1] if user_url else f"user_{timestamp}"
            
            # Comment content
            content_elem = comment_element.select_one(".comments-comment-item__main-content")
            content = content_elem.get_text().strip() if content_elem else ""
            
            # Like count
            like_count = 0
            like_elem = comment_element.select_one(".comments-comment-social-bar__reactions-count")
            if like_elem:
                like_text = like_elem.get_text().strip()
                like_match = re.search(r'(\d+)', like_text)
                if like_match:
                    like_count = int(like_match.group(1))
            
            # Parent comment ID for replies
            parent_comment_id = None
            if "comments-reply-item" in comment_element.get("class", []):
                # This is a reply, try to find parent
                parent_elem = comment_element.parent.parent
                parent_author = parent_elem.select_one(".comments-post-meta__name-text")
                if parent_author:
                    parent_comment_id = f"comment_{parent_author.get_text().strip()}"
            
            # Construct comment data
            comment_data = {
                "comment_id": comment_id,
                "post_id": post_id,
                "user_id": user_id,
                "content": content,
                "like_count": like_count,
                "reply_count": 0,  # Will be updated later
                "parent_comment_id": parent_comment_id,
                "published_at": datetime.utcnow(),
                "extra_data": {},
                "last_scraped": datetime.utcnow()
            }
            
            return comment_data
        except Exception as e:
            logger.error(f"Error extracting comment data: {e}")
            return {}
    
    async def scrape_employees(self, page_id: str) -> List[UserCreate]:
        """Scrape employees of a LinkedIn page"""
        if not self.driver:
            await self.initialize()
        
        employees_url = f"{self.base_url}/company/{page_id}/people"
        employees = []
        
        try:
            self.driver.get(employees_url)
            
            # Wait for employees to load
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".org-people-profile-card"))
                )
            except:
                # No employees found
                return []
            
            # Scroll to load more employees
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll a few times
            for _ in range(3):
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for content to load
                time.sleep(2)
                
                # Check if we've scrolled to the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                
                last_height = new_height
            
            # Get page HTML and extract employees
            employees_html = self.driver.page_source
            soup = BeautifulSoup(employees_html, "html.parser")
            
            employee_elements = soup.select(".org-people-profile-card")
            
            # Extract each employee
            for employee_elem in employee_elements:
                try:
                    employee_data = await self._extract_employee_data(employee_elem, page_id)
                    if employee_data and employee_data.get("user_id"):
                        employees.append(UserCreate(**employee_data))
                except Exception as e:
                    logger.error(f"Error extracting employee: {e}")
            
            logger.info(f"Scraped {len(employees)} employees for page {page_id}")
            return employees
        except Exception as e:
            logger.error(f"Error scraping employees for page {page_id}: {e}")
            return []
    
    async def _extract_employee_data(self, employee_element: Any, page_id: str) -> Dict[str, Any]:
        """Extract employee data from employee element"""
        try:
            # User profile link
            profile_link = employee_element.select_one(".org-people-profile-card__profile-title a")
            user_url = profile_link.get("href") if profile_link else ""
            user_id = user_url.split("/")[-1] if user_url else ""
            
            if not user_id:
                return {}
            
            # User name
            name = profile_link.get_text().strip() if profile_link else ""
            
            # Profile picture
            profile_picture = employee_element.select_one(".artdeco-entity-image")
            profile_picture_url = profile_picture.get("src") if profile_picture else None
            
            # Headline
            headline_elem = employee_element.select_one(".org-people-profile-card__subline")
            headline = headline_elem.get_text().strip() if headline_elem else ""
            
            # Location
            location_elem = employee_element.select_one(".org-people-profile-card__location")
            location = location_elem.get_text().strip() if location_elem else ""
            
            # Construct employee data
            employee_data = {
                "user_id": user_id,
                "url": urljoin(self.base_url, user_url) if user_url else f"{self.base_url}/in/{user_id}",
                "name": name,
                "profile_picture_url": profile_picture_url,
                "headline": headline,
                "company": None,  # Will be filled from page data
                "company_page_id": page_id,
                "location": location,
                "connection_count": None,
                "follower_count": None,
                "is_employee": True,
                "extra_data": {},
                "last_scraped": datetime.utcnow()
            }
            
            return employee_data
        except Exception as e:
            logger.error(f"Error extracting employee data: {e}")
            return {}
    
    async def scrape_all(self, page_id: str) -> Tuple[Optional[PageCreate], List[PostCreate], List[UserCreate], List[CommentCreate]]:
        """Scrape all LinkedIn page data: details, posts, employees, and comments"""
        if not self.driver:
            await self.initialize()
        
        # Try to login if credentials are provided
        if not self.is_logged_in and (settings.LINKEDIN_EMAIL and settings.LINKEDIN_PASSWORD):
            await self.login()
        
        # Scrape page details
        page = await self.scrape_page(page_id)
        if not page:
            logger.error(f"Failed to scrape page {page_id}")
            return None, [], [], []
        
        # Scrape posts
        posts = await self.scrape_posts(page_id)
        
        # Scrape employees
        employees = await self.scrape_employees(page_id)
        
        # Scrape comments for each post
        all_comments = []
        for post in posts[:5]:  # Limit to first 5 posts to avoid too many requests
            comments = await self.scrape_comments(post.post_id, post.url)
            all_comments.extend(comments)
        
        return page, posts, employees, all_comments 