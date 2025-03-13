import motor.motor_asyncio
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB client instance
client = None
# Database instance
db = None

async def connect_to_mongo():
    """Connect to MongoDB."""
    global client, db
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.MONGODB_DB_NAME]
        
        # Create collections if they don't exist
        if "pages" not in await db.list_collection_names():
            await db.create_collection("pages")
        
        if "posts" not in await db.list_collection_names():
            await db.create_collection("posts")
        
        if "users" not in await db.list_collection_names():
            await db.create_collection("users")
        
        if "comments" not in await db.list_collection_names():
            await db.create_collection("comments")
        
        # Create indexes
        await db.pages.create_indexes([
            IndexModel([("page_id", ASCENDING)], unique=True),
            IndexModel([("name", TEXT)]),
            IndexModel([("follower_count", ASCENDING)]),
            IndexModel([("industry", ASCENDING)])
        ])
        
        await db.posts.create_indexes([
            IndexModel([("page_id", ASCENDING)]),
            IndexModel([("post_id", ASCENDING)], unique=True),
            IndexModel([("published_at", DESCENDING)])
        ])
        
        await db.users.create_indexes([
            IndexModel([("user_id", ASCENDING)], unique=True),
            IndexModel([("name", TEXT)])
        ])
        
        await db.comments.create_indexes([
            IndexModel([("post_id", ASCENDING)]),
            IndexModel([("comment_id", ASCENDING)], unique=True)
        ])
        
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        logger.info("Closed MongoDB connection")

def get_database():
    """Get database instance."""
    return db 