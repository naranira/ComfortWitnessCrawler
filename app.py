import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///comfort_women_news.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# In-memory storage for articles (MVP version)
articles_storage = []
last_update = None

with app.app_context():
    # Import models and routes
    import models
    import routes
    from news_scraper import NewsScraperService
    
    # Create database tables
    db.create_all()
    
    # Initialize news scraper
    scraper = NewsScraperService()
    
    # Schedule periodic updates every 6 hours
    scheduler = BackgroundScheduler()
    
    def update_news():
        """Background task to update news articles"""
        with app.app_context():
            try:
                logging.info("Starting scheduled news update...")
                new_articles = scraper.scrape_all_sources()
                
                # Add new articles to storage (avoid duplicates)
                existing_urls = {article['url'] for article in articles_storage}
                for article in new_articles:
                    if article['url'] not in existing_urls:
                        articles_storage.append(article)
                
                # Keep only the latest 200 articles to manage memory
                articles_storage.sort(key=lambda x: x['published_date'], reverse=True)
                if len(articles_storage) > 200:
                    articles_storage[:] = articles_storage[:200]
                
                global last_update
                from datetime import datetime
                last_update = datetime.now()
                
                logging.info(f"News update completed. Total articles: {len(articles_storage)}")
            except Exception as e:
                logging.error(f"Error during scheduled news update: {e}")
    
    # Schedule updates every 6 hours
    scheduler.add_job(func=update_news, trigger="interval", hours=6, id='news_update')
    
    # Schedule an immediate job to scrape articles after startup
    scheduler.add_job(func=update_news, trigger="date", id='initial_scrape')
    
    scheduler.start()
    
    logging.info("Application started. Initial news scraping will begin in background...")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
