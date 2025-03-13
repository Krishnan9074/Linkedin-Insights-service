import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from app.main import app
from app.services.linkedin_service import LinkedInService
from app.models import PageInDB, PostInDB, UserInDB

client = TestClient(app)

@pytest.fixture
def mock_linkedin_service():
    """Fixture for mocking LinkedIn service"""
    service = AsyncMock(spec=LinkedInService)
    
    # Mock database
    service.db = MagicMock()
    
    # Sample page data
    page = PageInDB(
        page_id="test-company",
        name="Test Company",
        url="https://www.linkedin.com/company/test-company",
        profile_picture_url=None,
        description="This is a test company",
        website=None,
        industry="Technology",
        follower_count=1000,
        head_count=50,
        specialities=["Software", "Testing"],
        extra_data={},
        last_scraped="2023-01-01T00:00:00",
        linkedin_id=None,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )
    
    # Set up returns
    service.get_page.return_value = page
    service.scrape_page_data.return_value = (page, [], [], [])
    
    return service

@pytest.mark.asyncio
async def test_get_page(mock_linkedin_service):
    """Test get page endpoint"""
    with patch('app.api.routes.pages.get_linkedin_service', return_value=mock_linkedin_service):
        response = client.get("/api/pages/test-company")
        assert response.status_code == 200
        data = response.json()
        assert data["page_id"] == "test-company"
        assert data["name"] == "Test Company"
        assert data["follower_count"] == 1000

@pytest.mark.asyncio
async def test_list_pages(mock_linkedin_service):
    """Test list pages endpoint"""
    # Mock the query_pages method to return a paginated response
    page = mock_linkedin_service.get_page.return_value
    mock_linkedin_service.query_pages.return_value = {
        "items": [page],
        "total": 1,
        "page": 1,
        "limit": 10,
        "pages": 1
    }
    
    with patch('app.api.routes.pages.get_linkedin_service', return_value=mock_linkedin_service):
        response = client.get("/api/pages")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["page_id"] == "test-company"

@pytest.mark.asyncio
async def test_scrape_page_data(mock_linkedin_service):
    """Test scrape page data endpoint"""
    with patch('app.api.routes.pages.get_linkedin_service', return_value=mock_linkedin_service):
        response = client.post("/api/pages/test-company/scrape")
        assert response.status_code == 200
        data = response.json()
        assert data["page_id"] == "test-company"
        assert data["name"] == "Test Company"
        
        # Verify the scrape_page_data method was called
        mock_linkedin_service.scrape_page_data.assert_called_once_with("test-company") 