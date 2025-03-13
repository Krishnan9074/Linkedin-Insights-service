from fastapi import APIRouter
from app.api.routes import pages, posts, employees, comments, ai

router = APIRouter()

router.include_router(pages.router, prefix="/pages", tags=["pages"])
router.include_router(posts.router, prefix="/posts", tags=["posts"])
router.include_router(employees.router, prefix="/employees", tags=["employees"])
router.include_router(comments.router, prefix="/comments", tags=["comments"])
router.include_router(ai.router, prefix="/ai", tags=["ai"]) 