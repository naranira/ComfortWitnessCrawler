import requests
from bs4 import BeautifulSoup
import feedparser
import trafilatura
import time
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import re

class NewsScraperService:
    """Service for scraping news articles about Japanese military comfort women issues"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Keywords for filtering relevant articles
        self.keywords = [
            'comfort women', 'comfort woman', '위안부', 'wianbu',
            'japanese military', 'imperial japan', 'wartime sexual slavery',
            'sex slaves', 'sexual slavery', 'world war ii korea',
            'forced prostitution', 'military brothel', 'ianfu'
        ]
        
        # RSS feeds and news sources (Korean sources)
        self.rss_sources = [
            {
                'name': '연합뉴스',
                'url': 'https://www.yna.co.kr/rss/politics.xml',
                'category': 'Politics'
            },
            {
                'name': '한겨레',
                'url': 'http://www.hani.co.kr/rss/',
                'category': 'News'
            },
            {
                'name': '경향신문',
                'url': 'http://www.khan.co.kr/rss/rssdata/total_news.xml',
                'category': 'News'
            },
            {
                'name': '중앙일보',
                'url': 'https://rss.joins.com/joins_news_list.xml',
                'category': 'News'
            },
            {
                'name': 'KBS News',
                'url': 'http://world.kbs.co.kr/rss/rss_news.htm?lang=k',
                'category': 'Broadcasting'
            }
        ]
        
        # News websites to scrape (Korean sites)
        self.news_sites = [
            {
                'name': '조선일보',
                'base_url': 'https://www.chosun.com',
                'search_url': 'https://www.chosun.com/nsearch/',
                'category': 'News'
            },
            {
                'name': '동아일보',
                'base_url': 'https://www.donga.com',
                'search_url': 'https://www.donga.com/news/search',
                'category': 'News'
            },
            {
                'name': 'SBS News',
                'base_url': 'https://news.sbs.co.kr',
                'search_url': 'https://news.sbs.co.kr/news/search/main.do',
                'category': 'Broadcasting'
            }
        ]
    
    def is_relevant_article(self, title, content=None):
        """Check if article is relevant to comfort women issues"""
        text_to_check = (title + ' ' + (content or '')).lower()
        return any(keyword.lower() in text_to_check for keyword in self.keywords)
    
    def extract_article_content(self, url):
        """Extract full article content using trafilatura"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded)
                return content
        except Exception as e:
            logging.error(f"Error extracting content from {url}: {e}")
        return None
    
    def scrape_rss_feeds(self):
        """Scrape articles from RSS feeds"""
        articles = []
        
        for source in self.rss_sources:
            try:
                logging.info(f"Scraping RSS feed: {source['name']}")
                # Set timeout for RSS feeds
                feed = feedparser.parse(source['url'])
                
                for entry in feed.entries[:10]:  # Limit to 10 recent articles
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    
                    if self.is_relevant_article(title, summary):
                        # Extract publication date
                        pub_date = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                        else:
                            pub_date = datetime.now()
                        
                        # Extract full content
                        content = self.extract_article_content(entry.link)
                        
                        article = {
                            'title': title,
                            'summary': summary,
                            'content': content or summary,
                            'url': entry.link,
                            'source': source['name'],
                            'published_date': pub_date,
                            'category': source['category']
                        }
                        articles.append(article)
                        logging.info(f"Found relevant article: {title[:50]}...")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error scraping RSS feed {source['name']}: {e}")
        
        return articles
    
    def scrape_news_websites(self):
        """Scrape articles from news websites"""
        articles = []
        
        for site in self.news_sites:
            try:
                logging.info(f"Scraping website: {site['name']}")
                
                # Search for comfort women related articles
                search_terms = ['comfort women', '위안부', 'wartime sexual slavery']
                
                for term in search_terms:
                    try:
                        # Construct search URL (this is simplified - each site has different search patterns)
                        search_url = f"{site['search_url']}?q={term.replace(' ', '+')}"
                        
                        response = self.session.get(search_url, timeout=10)
                        response.raise_for_status()
                        
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Generic article link extraction (adapt per site)
                        article_links = []
                        
                        # Look for common article link patterns
                        for link in soup.find_all('a', href=True):
                            try:
                                href = link.get('href') if hasattr(link, 'get') else link.attrs.get('href', '')
                                text = link.get_text(strip=True) if hasattr(link, 'get_text') else str(link)
                                
                                if href and text and self.is_relevant_article(text):
                                    # Ensure href is a string before passing to urljoin
                                    href_str = str(href) if href else ''
                                    full_url = urljoin(site['base_url'], href_str)
                                    if full_url not in [a['url'] for a in articles]:
                                        article_links.append((full_url, text))
                            except Exception as e:
                                logging.error(f"Error processing link: {e}")
                                continue
                        
                        # Process found articles
                        for url, title in article_links[:5]:  # Limit to 5 per search term
                            try:
                                content = self.extract_article_content(url)
                                if content and self.is_relevant_article(title, content):
                                    article = {
                                        'title': title,
                                        'summary': content[:300] + '...' if len(content) > 300 else content,
                                        'content': content,
                                        'url': url,
                                        'source': site['name'],
                                        'published_date': datetime.now(),  # Fallback date
                                        'category': site['category']
                                    }
                                    articles.append(article)
                                    logging.info(f"Found article: {title[:50]}...")
                                
                                time.sleep(1)  # Rate limiting
                                
                            except Exception as e:
                                logging.error(f"Error processing article {url}: {e}")
                        
                        time.sleep(2)  # Rate limiting between searches
                        
                    except Exception as e:
                        logging.error(f"Error searching {site['name']} for '{term}': {e}")
                        continue
                
            except Exception as e:
                logging.error(f"Error scraping website {site['name']}: {e}")
        
        return articles
    
    def scrape_all_sources(self):
        """Scrape all configured news sources"""
        all_articles = []
        
        try:
            # Scrape RSS feeds
            rss_articles = self.scrape_rss_feeds()
            all_articles.extend(rss_articles)
            
            # Scrape news websites
            web_articles = self.scrape_news_websites()
            all_articles.extend(web_articles)
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_articles = []
            for article in all_articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            # Sort by publication date (newest first)
            unique_articles.sort(key=lambda x: x['published_date'], reverse=True)
            
            logging.info(f"Scraping completed. Found {len(unique_articles)} unique articles")
            return unique_articles
            
        except Exception as e:
            logging.error(f"Error during scraping: {e}")
            return []
