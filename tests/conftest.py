import pytest
from unittest.mock import MagicMock
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

@pytest.fixture
def mock_mongodb():
    """
    Fixture for mocking MongoDB connection
    """
    # Mock client
    client = MagicMock(spec=AsyncIOMotorClient)
    
    # Mock database
    db = MagicMock(spec=AsyncIOMotorDatabase)
    
    # Mock collections
    pages = MagicMock()
    posts = MagicMock()
    users = MagicMock()
    comments = MagicMock()
    ai_summaries = MagicMock()
    
    # Set up collections on db
    db.pages = pages
    db.posts = posts
    db.users = users
    db.comments = comments
    db.ai_summaries = ai_summaries
    
    # Set up db on client
    client.__getitem__.return_value = db
    
    return client, db 