from flask import render_template, request, jsonify, url_for
from app import app, articles_storage, last_update
import logging
from datetime import datetime

@app.route('/')
def index():
    """Main page showing latest articles"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get articles for current page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_articles = articles_storage[start_idx:end_idx]
    
    # Calculate pagination info
    total_articles = len(articles_storage)
    has_prev = page > 1
    has_next = end_idx < total_articles
    
    return render_template('index.html',
                         articles=page_articles,
                         page=page,
                         has_prev=has_prev,
                         has_next=has_next,
                         total_articles=total_articles,
                         last_update=last_update)

@app.route('/article/<path:url>')
def article_detail(url):
    """Show detailed view of a specific article"""
    # Find article by URL
    article = None
    for a in articles_storage:
        if a['url'] == url:
            article = a
            break
    
    if not article:
        return render_template('article.html', article=None, error="Article not found")
    
    return render_template('article.html', article=article)

@app.route('/search')
def search():
    """Search articles by keyword"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    source = request.args.get('source', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Filter articles based on search criteria
    filtered_articles = articles_storage.copy()
    
    if query:
        query_lower = query.lower()
        filtered_articles = [
            article for article in filtered_articles
            if query_lower in article['title'].lower() or
               query_lower in article.get('summary', '').lower() or
               query_lower in article.get('content', '').lower()
        ]
    
    if category:
        filtered_articles = [
            article for article in filtered_articles
            if article.get('category', '').lower() == category.lower()
        ]
    
    if source:
        filtered_articles = [
            article for article in filtered_articles
            if article.get('source', '').lower() == source.lower()
        ]
    
    # Pagination
    total_results = len(filtered_articles)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_articles = filtered_articles[start_idx:end_idx]
    
    has_prev = page > 1
    has_next = end_idx < total_results
    
    # Get available categories and sources for filters
    categories = list(set(article.get('category', '') for article in articles_storage if article.get('category')))
    sources = list(set(article.get('source', '') for article in articles_storage if article.get('source')))
    
    return render_template('search.html',
                         articles=page_articles,
                         query=query,
                         category=category,
                         source=source,
                         page=page,
                         has_prev=has_prev,
                         has_next=has_next,
                         total_results=total_results,
                         categories=categories,
                         sources=sources)

@app.route('/refresh')
def refresh_articles():
    """Manually trigger article refresh"""
    try:
        from news_scraper import NewsScraperService
        scraper = NewsScraperService()
        
        logging.info("Manual refresh triggered")
        new_articles = scraper.scrape_all_sources()
        
        # Add new articles to storage (avoid duplicates)
        existing_urls = {article['url'] for article in articles_storage}
        added_count = 0
        
        for article in new_articles:
            if article['url'] not in existing_urls:
                articles_storage.append(article)
                added_count += 1
        
        # Sort by date and limit articles
        articles_storage.sort(key=lambda x: x['published_date'], reverse=True)
        if len(articles_storage) > 200:
            articles_storage[:] = articles_storage[:200]
        
        global last_update
        last_update = datetime.now()
        
        return jsonify({
            'success': True,
            'message': f'Added {added_count} new articles. Total: {len(articles_storage)}',
            'total_articles': len(articles_storage)
        })
        
    except Exception as e:
        logging.error(f"Error during manual refresh: {e}")
        return jsonify({
            'success': False,
            'message': f'Error refreshing articles: {str(e)}'
        }), 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for article statistics"""
    categories = {}
    sources = {}
    
    for article in articles_storage:
        cat = article.get('category', 'Uncategorized')
        source = article.get('source', 'Unknown')
        
        categories[cat] = categories.get(cat, 0) + 1
        sources[source] = sources.get(source, 0) + 1
    
    return jsonify({
        'total_articles': len(articles_storage),
        'categories': categories,
        'sources': sources,
        'last_update': last_update.isoformat() if last_update else None
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html', error="Internal server error"), 500
