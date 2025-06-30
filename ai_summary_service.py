import os
import json
import logging
from typing import List, Dict, Optional
import requests
from google.auth import default
from google.auth.transport.requests import Request
import google.auth

class VertexAISummaryService:
    """Service for generating AI summaries using Vertex AI Search"""
    
    def __init__(self):
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        self.search_config_id = os.environ.get('VERTEX_AI_SEARCH_CONFIG_ID')
        self.credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Set up authentication
        self._setup_authentication()
        
    def _setup_authentication(self):
        """Setup Google Cloud authentication"""
        try:
            if self.credentials_path:
                # If credentials file is provided as JSON string, save it
                if self.credentials_path.startswith('{'):
                    with open('/tmp/google_credentials.json', 'w') as f:
                        f.write(self.credentials_path)
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/google_credentials.json'
                    
            # Get default credentials
            self.credentials, _ = default()
            logging.info("Google Cloud authentication setup successful")
        except Exception as e:
            logging.error(f"Failed to setup Google Cloud authentication: {e}")
            self.credentials = None
    
    def _get_access_token(self) -> Optional[str]:
        """Get access token for API calls"""
        if not self.credentials:
            return None
            
        try:
            self.credentials.refresh(Request())
            return self.credentials.token
        except Exception as e:
            logging.error(f"Failed to get access token: {e}")
            return None
    
    def generate_summary(self, articles: List[Dict]) -> Optional[str]:
        """Generate a summary of recent articles using Vertex AI"""
        if not self.project_id or not self.search_config_id or not articles:
            return None
            
        try:
            # Prepare article texts for summarization
            article_texts = []
            for article in articles[:5]:  # Use only the 5 most recent articles
                text = f"Title: {article.get('title', '')}\n"
                if article.get('summary'):
                    text += f"Summary: {article['summary']}\n"
                elif article.get('content'):
                    text += f"Content: {article['content'][:500]}...\n"
                text += f"Source: {article.get('source', '')}\n"
                text += f"Date: {article.get('published_date', '')}\n\n"
                article_texts.append(text)
            
            combined_text = "\n".join(article_texts)
            
            # Generate summary using Vertex AI Generative AI
            summary = self._generate_ai_summary(combined_text)
            return summary
            
        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            return None
    
    def _generate_ai_summary(self, text: str) -> Optional[str]:
        """Generate AI summary using Vertex AI API"""
        access_token = self._get_access_token()
        if not access_token:
            return None
            
        try:
            # Use Vertex AI PaLM API for text generation
            url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/us-central1/publishers/google/models/text-bison:predict"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            prompt = f"""다음은 일본군 위안부 문제와 관련된 최신 뉴스 기사들입니다. 이 기사들을 바탕으로 한국어로 간결하고 포괄적인 요약을 작성해주세요.

{text}

요약 작성 지침:
- 한국어로 작성해주세요
- 주요 사건이나 발표 내용을 포함해주세요
- 3-4 문장으로 간결하게 요약해주세요
- 객관적이고 정확한 정보만 포함해주세요

요약:"""

            payload = {
                "instances": [
                    {
                        "prompt": prompt
                    }
                ],
                "parameters": {
                    "temperature": 0.3,
                    "maxOutputTokens": 200,
                    "topK": 40,
                    "topP": 0.8
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'predictions' in result and len(result['predictions']) > 0:
                    summary = result['predictions'][0].get('content', '').strip()
                    return summary if summary else None
            else:
                logging.error(f"Vertex AI API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logging.error(f"Error calling Vertex AI API: {e}")
            
        return None
    
    def search_articles(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for articles using Vertex AI Search"""
        if not self.project_id or not self.search_config_id:
            return []
            
        access_token = self._get_access_token()
        if not access_token:
            return []
            
        try:
            # Use Vertex AI Search API
            url = f"https://discoveryengine.googleapis.com/v1/projects/{self.project_id}/locations/global/collections/default_collection/dataStores/{self.search_config_id}/servingConfigs/default_config:search"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "query": query,
                "pageSize": max_results,
                "queryExpansionSpec": {
                    "condition": "AUTO"
                },
                "spellCorrectionSpec": {
                    "mode": "AUTO"
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                # Process search results
                articles = []
                for item in result.get('results', []):
                    document = item.get('document', {})
                    derived_struct = document.get('derivedStructData', {})
                    
                    article = {
                        'title': derived_struct.get('title', ''),
                        'summary': derived_struct.get('snippet', ''),
                        'url': derived_struct.get('link', ''),
                        'source': 'Vertex AI Search'
                    }
                    articles.append(article)
                
                return articles
            else:
                logging.error(f"Vertex AI Search API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logging.error(f"Error calling Vertex AI Search API: {e}")
            
        return []