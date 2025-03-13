import json
import redis.asyncio as redis
from app.core.config import settings
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Redis client instance
redis_client = None

async def get_redis_client():
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            await redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Could not connect to Redis: {e}")
            redis_client = None
    return redis_client

async def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache
    """
    client = await get_redis_client()
    if client is None:
        return None
    
    try:
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Error getting from cache: {e}")
        return None

async def set_cache(key: str, value: Any, ttl: int = None) -> bool:
    """
    Set value in cache with optional TTL (seconds)
    """
    if ttl is None:
        ttl = settings.CACHE_TTL
        
    client = await get_redis_client()
    if client is None:
        return False
    
    try:
        await client.set(key, json.dumps(value), ex=ttl)
        return True
    except Exception as e:
        logger.error(f"Error setting cache: {e}")
        return False

async def delete_cache(key: str) -> bool:
    """
    Delete value from cache
    """
    client = await get_redis_client()
    if client is None:
        return False
    
    try:
        await client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error deleting from cache: {e}")
        return False 