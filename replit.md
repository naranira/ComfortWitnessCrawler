# Comfort Women News Aggregator

## Overview

This is a Flask-based web application that aggregates news articles about Japanese military comfort women issues. The system scrapes articles from various RSS feeds and news sources, stores them in memory (MVP version), and provides a web interface for browsing and searching articles.

## System Architecture

The application follows a simple Flask MVC architecture with the following key components:

- **Backend**: Flask web application with SQLAlchemy ORM
- **Frontend**: Server-side rendered HTML templates using Jinja2
- **Data Storage**: SQLite database (configured via SQLAlchemy) with in-memory storage for MVP
- **News Scraping**: Custom news scraper service using RSS feeds and web scraping
- **Scheduling**: Background scheduler for periodic news updates
- **Styling**: Bootstrap with dark theme and Font Awesome icons

## Key Components

### Backend Components

1. **Flask Application** (`app.py`, `main.py`)
   - Main Flask application setup with database configuration
   - Environment-based configuration for database URL and session secrets
   - Background scheduler initialization for periodic news updates
   - Production-ready with ProxyFix middleware

2. **Database Models** (`models.py`)
   - `Article` model with comprehensive fields (title, summary, content, URL, source, dates, category)
   - SQLAlchemy ORM with DeclarativeBase
   - Prepared for future database persistence (currently using in-memory storage)

3. **News Scraper Service** (`news_scraper.py`)
   - Multi-source news aggregation from RSS feeds and websites
   - Keyword-based filtering for relevant comfort women articles
   - Sources include Korean Central News Agency, Yonhap News, Korea Herald, Japan Times
   - Uses requests, BeautifulSoup, feedparser, and trafilatura for content extraction

4. **Routes** (`routes.py`)
   - Home page with pagination support
   - Article detail view
   - Search functionality with filtering by category and source
   - RESTful URL structure

### Frontend Components

1. **Templates**
   - `base.html`: Bootstrap-based layout with dark theme and responsive navigation
   - `index.html`: Article listing with pagination, summary cards, and AI-powered news summary
   - `article.html`: Detailed article view with breadcrumbs
   - `search.html`: Advanced search interface with filters
   - `archive.html`: Date-organized article archive with enhanced browsing

2. **Static Assets**
   - `custom.css`: Enhanced styling with hover effects and responsive design
   - `main.js`: Client-side enhancements including tooltips, smooth scrolling, and form improvements

## Data Flow

1. **News Collection**: Background scheduler triggers news scraper every 6 hours
2. **Content Processing**: Scraper fetches articles from RSS feeds and websites, filters by keywords
3. **Storage**: Articles stored in in-memory list (MVP) with database model ready for persistence
4. **Display**: Web interface renders articles with pagination and search capabilities
5. **User Interaction**: Users browse, search, and view detailed articles through responsive web interface

## External Dependencies

### Python Packages
- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **APScheduler**: Background task scheduling
- **Requests**: HTTP client for web scraping
- **BeautifulSoup4**: HTML parsing
- **Feedparser**: RSS feed parsing
- **Trafilatura**: Content extraction

### Frontend Dependencies
- **Bootstrap**: UI framework with Replit dark theme
- **Font Awesome**: Icon library
- **jQuery**: JavaScript utilities (via Bootstrap)

### News Sources
- Korean Central News Agency (RSS)
- Yonhap News (RSS)
- Korea Herald (RSS)
- Japan Times (web scraping)

## Deployment Strategy

The application is configured for deployment with:

- **Environment Variables**: `DATABASE_URL`, `SESSION_SECRET`
- **Production Settings**: ProxyFix middleware for reverse proxy compatibility
- **Database**: SQLite for development, configurable for PostgreSQL in production
- **Logging**: Comprehensive logging with DEBUG level
- **Port Configuration**: Runs on port 5000 with host 0.0.0.0 for container compatibility

## Changelog

Changelog:
- June 30, 2025. Initial setup
- June 30, 2025. Added archive page for browsing all articles by date
- June 30, 2025. Integrated Vertex AI Search for AI-powered news summaries on homepage

## User Preferences

Preferred communication style: Simple, everyday language.