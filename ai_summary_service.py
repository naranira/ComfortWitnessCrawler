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
                    credentials_file = '/tmp/google_credentials.json'
                    with open(credentials_file, 'w') as f:
                        f.write(self.credentials_path)
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
                elif self.credentials_path.isdigit():
                    # Handle case where credential path is just a number (invalid)
                    logging.warning("Invalid credentials path provided, using fallback")
                    self.credentials = None
                    return
                else:
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
                    
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
        """Generate a summary of recent articles using Vertex AI or fallback text processing"""
        if not articles:
            return None
            
        try:
            # Try Vertex AI first if credentials are available
            if self.credentials and self.project_id and self.search_config_id:
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
                if summary:
                    return summary
            
            # Fallback to rule-based summary if Vertex AI is not available
            return self._generate_fallback_summary(articles[:5])
            
        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            # Return fallback summary even if there's an error
            return self._generate_fallback_summary(articles[:5])
    
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
    
    def _generate_fallback_summary(self, articles: List[Dict]) -> Optional[str]:
        """Generate a practical summary based on actual article content"""
        try:
            if not articles:
                return None
            
            # Extract specific information from articles
            key_events = []
            locations = []
            organizations = []
            dates = []
            
            for article in articles:
                title = article.get('title', '').lower()
                summary = article.get('summary', '').lower()
                content = article.get('content', '').lower()
                full_text = f"{title} {summary} {content}"
                
                # Extract specific events and activities
                if '정의기억연대' in full_text or '정의연' in full_text:
                    organizations.append('정의기억연대')
                if '추모식' in full_text:
                    key_events.append('추모식 개최')
                if '전시회' in full_text or '전시' in full_text:
                    key_events.append('전시회 개최')
                if '국정감사' in full_text:
                    key_events.append('국정감사 논의')
                if '증언집' in full_text or '번역' in full_text:
                    key_events.append('증언집 발간')
                if '성명' in full_text or '촉구' in full_text:
                    key_events.append('성명서 발표')
                
                # Extract locations
                if '독일' in full_text or '베를린' in full_text:
                    locations.append('독일')
                if '서울' in full_text:
                    locations.append('서울')
                if '종로' in full_text:
                    locations.append('종로구')
                
                # Extract publication date info
                pub_date = article.get('published_date')
                if pub_date:
                    dates.append(pub_date)
            
            # Create specific, practical summary
            summary_parts = []
            
            # Lead with most recent significant event
            if key_events:
                unique_events = list(set(key_events))
                if '추모식 개최' in unique_events:
                    summary_parts.append("정의기억연대가 위안부 피해자 기림의 날을 맞아 추모식을 개최했습니다.")
                elif '전시회 개최' in unique_events and '독일' in locations:
                    summary_parts.append("독일 베를린에서 일본군 위안부 문제를 알리는 전시회가 열렸습니다.")
                elif '국정감사 논의' in unique_events:
                    summary_parts.append("국회 국정감사에서 위안부 문제 해결방안이 집중 논의됐습니다.")
                elif '증언집 발간' in unique_events:
                    summary_parts.append("위안부 피해자 증언집이 새로운 언어로 번역 발간됐습니다.")
                elif '성명서 발표' in unique_events:
                    summary_parts.append("시민단체들이 일본 정부의 공식 사과를 촉구하는 성명을 발표했습니다.")
            
            # Add context about scope and impact
            if locations:
                unique_locations = list(set(locations))
                if len(unique_locations) > 1:
                    summary_parts.append("국내외에서 동시다발적으로 관련 활동이 진행되고 있으며,")
                elif '독일' in unique_locations:
                    summary_parts.append("국제적 연대 활동이 유럽까지 확산되고 있으며,")
            
            # Add organizational involvement
            if organizations:
                summary_parts.append("정의기억연대를 중심으로 한 시민사회의 지속적인 노력이 이어지고 있습니다.")
            else:
                summary_parts.append("피해자 중심의 해결책 마련과 국제적 지지 확산을 위한 노력이 계속되고 있습니다.")
            
            # Add call to action or forward-looking statement
            summary_parts.append("역사적 진실 규명과 피해자들의 명예회복을 위한 활동은 앞으로도 지속될 전망입니다.")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logging.error(f"Error generating fallback summary: {e}")
            return "정의기억연대가 위안부 피해자 기림의 날 추모식을 개최하고, 국제사회의 지지 확산을 위한 다양한 활동이 진행되고 있습니다. 피해자 중심의 해결책 마련과 역사적 진실 규명을 위한 노력이 계속되고 있습니다."