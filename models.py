from app import db
from datetime import datetime

class Article(db.Model):
    """Article model for storing news articles in database if needed in future"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    summary = db.Column(db.Text)
    content = db.Column(db.Text)
    url = db.Column(db.String(1000), unique=True, nullable=False)
    source = db.Column(db.String(200), nullable=False)
    published_date = db.Column(db.DateTime, nullable=False)
    scraped_date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Article {self.title[:50]}...>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'content': self.content,
            'url': self.url,
            'source': self.source,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'scraped_date': self.scraped_date.isoformat() if self.scraped_date else None,
            'category': self.category
        }
