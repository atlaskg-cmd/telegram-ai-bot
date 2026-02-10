"""
AI News Aggregator with Sentiment Analysis
Parses RSS from 20+ sources, classifies news, analyzes sentiment
"""

import asyncio
import aiohttp
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import re
import json

# RSS Sources by category
RSS_SOURCES = {
    "tech": [
        "https://habr.com/ru/rss/all/all/",
        "https://www.engadget.com/rss.xml",
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
    ],
    "ai": [
        "https://www.marktechpost.com/feed/",
        "https://towardsdatascience.com/feed",
        "https://openai.com/blog/rss.xml",
    ],
    "science": [
        "https://www.sciencedaily.com/rss/all.xml",
        "https://phys.org/rss-feed/",
    ],
    "space": [
        "https://www.spacex.com/updates",
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    ],
    "finance": [
        "https://finance.yahoo.com/news/rssindex",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
    ],
    "kyrgyzstan": [
        "https://kaktus.media/?rss",
        "https://24.kg/rss/",
        "https://www.akipress.org/rss/",
    ],
    "world": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.cnn.com/rss/edition_world.rss",
    ],
    "sports": [
        "https://www.espn.com/espn/rss/news",
    ],
}

# Category keywords for AI classification
CATEGORY_KEYWORDS = {
    "tech": ["технолог", "technology", "software", "hardware", "app", "программ", "ai", "кибер"],
    "ai": ["искусственный интеллект", "machine learning", "deep learning", "neural", "нейросет", "chatgpt", "llm", "модель"],
    "science": ["наука", "science", "research", "исследован", "discovery"],
    "space": ["космос", "space", "spacex", "nasa", "rocket", "ракет", "марс", "mars"],
    "finance": ["финанс", "finance", "crypto", "bitcoin", "экономик", "market", "биржа"],
    "kyrgyzstan": ["кыргызстан", "бишкек", "кыргыз", "kg"],
    "world": ["мир", "world", "политик", "politic", "war", "война"],
    "sports": ["спорт", "football", "soccer", "nba", "olympic"],
}


class NewsAggregator:
    def __init__(self, db):
        self.db = db
        self.session = None
        
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'}
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_rss(self, url: str) -> Optional[str]:
        """Fetch RSS feed content"""
        try:
            await self.init_session()
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logging.warning(f"RSS fetch failed {url}: {response.status}")
                    return None
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_rss_feed(self, content: str, source_category: str) -> List[Dict]:
        """Parse RSS content and extract news items"""
        if not content:
            return []
        
        try:
            feed = feedparser.parse(content)
            items = []
            
            for entry in feed.entries[:10]:  # Last 10 items
                # Extract publish date
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])
                else:
                    published = datetime.now()
                
                # Skip old news (older than 3 days)
                if datetime.now() - published > timedelta(days=3):
                    continue
                
                item = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', entry.get('description', ''))[:500],
                    'published': published,
                    'source_category': source_category,
                    'source_name': feed.feed.get('title', 'Unknown'),
                }
                items.append(item)
            
            return items
        except Exception as e:
            logging.error(f"Error parsing RSS: {e}")
            return []
    
    def classify_category(self, title: str, summary: str = "") -> str:
        """Classify news into category based on keywords"""
        text = (title + " " + summary).lower()
        
        scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "other"
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    async def analyze_sentiment_openrouter(self, title: str, summary: str) -> Dict:
        """Analyze sentiment using OpenRouter AI"""
        try:
            import os
            import requests
            
            api_key = os.environ.get("OPENROUTER_API_KEY", "")
            if not api_key:
                return {"sentiment": "neutral", "score": 0.0, "explanation": "No API key"}
            
            prompt = f"""Analyze the sentiment of this news article.
Title: {title}
Summary: {summary}

Respond ONLY in JSON format:
{{
    "sentiment": "positive" | "negative" | "neutral",
    "score": -1.0 to 1.0,
    "explanation": "brief reason"
}}"""
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.5-flash-lite",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Extract JSON from response
                try:
                    # Try to find JSON in the response
                    json_match = re.search(r'\{[^}]+\}', content)
                    if json_match:
                        return json.loads(json_match.group())
                except:
                    pass
                
                return {"sentiment": "neutral", "score": 0.0, "explanation": content[:100]}
            else:
                return {"sentiment": "neutral", "score": 0.0, "explanation": "API error"}
                
        except Exception as e:
            logging.error(f"Sentiment analysis error: {e}")
            return {"sentiment": "neutral", "score": 0.0, "explanation": "Error"}
    
    async def collect_all_news(self) -> List[Dict]:
        """Collect news from all sources"""
        all_news = []
        
        for category, urls in RSS_SOURCES.items():
            for url in urls:
                content = await self.fetch_rss(url)
                if content:
                    items = self.parse_rss_feed(content, category)
                    for item in items:
                        # Classify category
                        item['category'] = self.classify_category(
                            item['title'], 
                            self.clean_html(item['summary'])
                        )
                        # Clean summary
                        item['summary'] = self.clean_html(item['summary'])
                        all_news.append(item)
        
        # Remove duplicates by link
        seen_links = set()
        unique_news = []
        for item in all_news:
            if item['link'] not in seen_links:
                seen_links.add(item['link'])
                unique_news.append(item)
        
        logging.info(f"Collected {len(unique_news)} unique news items")
        return unique_news
    
    async def process_and_save_news(self):
        """Collect, analyze and save news to database"""
        news_items = await self.collect_all_news()
        
        saved_count = 0
        for item in news_items:
            # Analyze sentiment (limited to avoid API overload)
            if saved_count < 10:  # Only for first 10 to save API calls
                sentiment = await self.analyze_sentiment_openrouter(
                    item['title'], item['summary']
                )
                item['sentiment'] = sentiment.get('sentiment', 'neutral')
                item['sentiment_score'] = sentiment.get('score', 0.0)
            else:
                item['sentiment'] = 'neutral'
                item['sentiment_score'] = 0.0
            
            # Save to database
            if self.db.save_news_item(item):
                saved_count += 1
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        logging.info(f"Saved {saved_count} news items to database")
        return saved_count
    
    def generate_digest(self, user_interests: List[str], limit: int = 10) -> str:
        """Generate personalized digest for user"""
        news = self.db.get_news_by_categories(user_interests, limit)
        
        if not news:
            return "📰 Нет новостей по вашим интересам за последние 3 дня."
        
        digest_parts = ["📰 <b>Ваш персональный дайджест</b>\n"]
        
        for item in news:
            # Emoji by sentiment
            sentiment_emoji = {
                'positive': '😊',
                'negative': '😟',
                'neutral': '😐'
            }.get(item['sentiment'], '😐')
            
            # Emoji by category
            category_emoji = {
                'tech': '💻',
                'ai': '🤖',
                'science': '🔬',
                'space': '🚀',
                'finance': '💰',
                'kyrgyzstan': '🇰🇬',
                'world': '🌍',
                'sports': '⚽',
                'other': '📄'
            }.get(item['category'], '📄')
            
            digest_parts.append(
                f"\n{category_emoji} <b>{item['title']}</b> {sentiment_emoji}\n"
                f"📂 {item['category'].upper()} | 📅 {item['published'][:10]}\n"
                f"📝 {item['summary'][:200]}...\n"
                f"🔗 <a href='{item['link']}'>Читать далее</a>\n"
            )
        
        return "\n".join(digest_parts)


# Simple keyword-based sentiment fallback
def simple_sentiment_analysis(text: str) -> Dict:
    """Simple sentiment analysis without API"""
    positive_words = ['отлично', 'хорошо', 'успех', 'рост', 'победа', 'breakthrough', 'success', 'growth', 'win']
    negative_words = ['плохо', 'кризис', 'падение', 'смерть', 'война', 'crisis', 'crash', 'death', 'war', 'fail']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return {"sentiment": "positive", "score": 0.5}
    elif negative_count > positive_count:
        return {"sentiment": "negative", "score": -0.5}
    else:
        return {"sentiment": "neutral", "score": 0.0}
