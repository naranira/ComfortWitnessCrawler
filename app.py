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
    
    # Add some sample articles for testing if no articles exist
    def add_sample_articles():
        """Add sample articles for testing purposes"""
        if len(articles_storage) == 0:
            from datetime import datetime, timedelta
            sample_articles = [
                {
                    'title': '정의기억연대, 위안부 피해자 기림의 날 추모식 개최',
                    'summary': '정의기억연대가 일본군 위안부 피해자 기림의 날을 맞아 추모식을 개최했다. 피해자들의 명예회복과 역사적 진실 규명을 위한 지속적인 노력이 필요하다고 강조했다.',
                    'content': '정의기억연대(정의연)는 14일 일본군 위안부 피해자 기림의 날을 맞아 서울 종로구 옛 일본대사관 앞에서 추모식을 개최했다고 밝혔다. 이날 추모식에는 위안부 피해 생존자와 시민들이 참석해 희생자들을 추모하고 역사적 진실 규명의 중요성을 다시 한번 확인했다.',
                    'url': 'https://example.com/article1',
                    'source': '연합뉴스',
                    'published_date': datetime.now() - timedelta(hours=2),
                    'category': 'Social'
                },
                {
                    'title': '일본 정부, 위안부 문제 공식 사과 촉구 시민단체 성명',
                    'summary': '시민단체들이 일본 정부의 공식적인 사과와 법적 배상을 요구하는 성명을 발표했다. 국제사회의 지속적인 관심과 압력이 필요하다고 주장했다.',
                    'content': '전국 여성단체들이 연합하여 일본군 위안부 문제에 대한 일본 정부의 공식 사과와 법적 배상을 촉구하는 성명서를 발표했다. 성명서에서는 피해자 중심의 해결방안 마련과 역사교육 강화의 필요성을 강조했다.',
                    'url': 'https://example.com/article2',
                    'source': '한겨레',
                    'published_date': datetime.now() - timedelta(hours=5),
                    'category': 'Politics'
                },
                {
                    'title': '독일서 위안부 문제 알리는 전시회 개최',
                    'summary': '독일 베를린에서 일본군 위안부 문제를 알리는 사진전시회가 열렸다. 유럽 시민들의 큰 관심을 받으며 국제적 연대의 중요성을 보여줬다.',
                    'content': '독일 베를린 시내 갤러리에서 일본군 위안부 피해자들의 삶과 투쟁을 다룬 사진전시회가 개막했다. 이번 전시회는 한국정신대문제대책협의회와 독일 현지 시민단체가 공동 주최했으며, 많은 독일 시민들이 관심을 보이고 있다.',
                    'url': 'https://example.com/article3',
                    'source': 'KBS News',
                    'published_date': datetime.now() - timedelta(hours=8),
                    'category': 'International'
                },
                {
                    'title': '위안부 피해자 증언집 새 번역본 발간',
                    'summary': '일본군 위안부 피해자들의 증언을 담은 책이 새로운 언어로 번역되어 발간됐다. 전 세계적으로 역사적 진실을 알리는 데 기여할 것으로 기대된다.',
                    'content': '일본군 위안부 피해자 할머니들의 생생한 증언을 담은 증언집이 스페인어와 프랑스어로 번역되어 발간됐다. 이로써 더 많은 국가의 사람들이 위안부 문제의 진실에 접근할 수 있게 됐다.',
                    'url': 'https://example.com/article4',
                    'source': '경향신문',
                    'published_date': datetime.now() - timedelta(hours=12),
                    'category': 'Culture'
                },
                {
                    'title': '국정감사서 위안부 문제 해결방안 논의',
                    'summary': '국회 국정감사에서 일본군 위안부 문제 해결을 위한 정부의 노력과 향후 계획이 집중 논의됐다.',
                    'content': '국회 여성가족위원회 국정감사에서 일본군 위안부 문제 해결을 위한 정부의 정책과 향후 계획이 집중적으로 논의됐다. 의원들은 피해자 중심의 해결책 마련과 국제적 연대 강화를 주문했다.',
                    'url': 'https://example.com/article5',
                    'source': '중앙일보',
                    'published_date': datetime.now() - timedelta(hours=18),
                    'category': 'Politics'
                },
                {
                    'title': '기지촌 여성 인권침해 실태조사 결과 발표',
                    'summary': '미군기지 주변 기지촌에서 일어난 여성 인권침해 실태조사 결과가 발표됐다. 체계적인 지원방안 마련이 시급하다는 지적이 나왔다.',
                    'content': '국가인권위원회가 실시한 기지촌 여성 인권침해 실태조사 결과가 발표됐다. 조사에 따르면 1960-80년대 미군기지 주변에서 성매매에 종사했던 여성들이 겪은 인권침해가 심각한 수준이었던 것으로 나타났다.',
                    'url': 'https://example.com/article6',
                    'source': '한겨레',
                    'published_date': datetime.now() - timedelta(hours=24),
                    'category': 'Human Rights'
                },
                {
                    'title': '미군 위안부 피해자들의 증언 다큐멘터리 제작',
                    'summary': '기지촌 여성들의 생생한 증언을 담은 다큐멘터리가 제작됐다. 숨겨진 역사의 진실을 알리는 데 기여할 것으로 기대된다.',
                    'content': '1970년대 평택, 의정부 등 미군기지 주변 기지촌에서 생활했던 여성들의 증언을 담은 다큐멘터리 "잊혀진 목소리"가 제작됐다. 이 작품은 그동안 조명받지 못했던 미군 위안부 문제를 다루고 있다.',
                    'url': 'https://example.com/article7',
                    'source': 'SBS News',
                    'published_date': datetime.now() - timedelta(hours=30),
                    'category': 'Culture'
                }
            ]
            
            articles_storage.extend(sample_articles)
            global last_update
            last_update = datetime.now()
            logging.info(f"Added {len(sample_articles)} sample articles for demonstration")
    
    # Add sample articles first
    add_sample_articles()
    
    # Schedule an immediate job to scrape articles after startup
    scheduler.add_job(func=update_news, trigger="date", id='initial_scrape')
    
    scheduler.start()
    
    logging.info("Application started. Sample articles loaded, real news scraping will begin in background...")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
