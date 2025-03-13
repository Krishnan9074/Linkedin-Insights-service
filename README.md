# LinkedIn Insights Microservice

A microservice application to scrape and analyze LinkedIn page data, providing various insights through a RESTful API interface.

## Features

- **LinkedIn Scraper**: Scrapes page details, posts, comments, and employee information
- **Data Storage**: Stores scraped data in MongoDB with appropriate schema relationships
- **API Endpoints**: RESTful APIs for querying LinkedIn page insights
- **Filtering & Pagination**: Filter pages by followers, industry, and more with paginated results
- **Caching**: Redis-based caching with TTL for improved performance

## Tech Stack

- **Backend**: FastAPI
- **Database**: MongoDB
- **Scraping**: Selenium, BeautifulSoup4
- **Caching**: Redis
- **Testing**: Pytest
- **Containerization**: Docker

## Project Structure

```
linkedin-insights/
├── app/
│   ├── api/                   # API routes
│   ├── core/                  # Core configuration
│   ├── db/                    # Database modules
│   ├── models/                # Pydantic models
│   ├── schemas/               # MongoDB schemas
│   ├── scraper/               # LinkedIn scraping functionality
│   └── services/              # Business logic services
├── tests/                     # Test suite
├── .env                       # Environment variables
├── docker-compose.yml         # Docker compose configuration
├── Dockerfile                 # Docker configuration
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

## Setup and Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/linkedin-insights.git
cd linkedin-insights
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

### Docker Setup

1. Build and run with Docker Compose:
```bash
docker-compose up -d
```
## API Documentation

Once the application is running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc


## Main Endpoints

- `GET /api/pages/{page_id}` - Get details of a LinkedIn page
- `GET /api/pages` - List pages with filtering options
- `GET /api/pages/{page_id}/posts` - Get posts from a LinkedIn page
- `GET /api/pages/{page_id}/employees` - Get employees of a LinkedIn page
