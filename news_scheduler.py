"""
News Scheduler - Background tasks for news aggregation and digest delivery
"""

import asyncio
from datetime import datetime
import logging
from news_aggregator import NewsAggregator


class NewsScheduler:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.aggregator = NewsAggregator(db)
        self.running = False
        
    async def start(self):
        """Start background tasks"""
        self.running = True
        logging.info("News scheduler started")
        
        # Run two tasks concurrently
        await asyncio.gather(
            self.collect_news_task(),
            self.send_digests_task()
        )
    
    async def collect_news_task(self):
        """Collect news every hour"""
        while self.running:
            try:
                logging.info("Starting news collection...")
                count = await self.aggregator.process_and_save_news()
                logging.info(f"Collected {count} news items")
            except Exception as e:
                logging.error(f"Error in news collection: {e}")
            
            # Wait 1 hour before next collection
            await asyncio.sleep(3600)
    
    async def send_digests_task(self):
        """Check and send digests every minute"""
        while self.running:
            try:
                current_time = datetime.now().strftime("%H:%M")
                users = self.db.get_users_for_digest(current_time)
                
                for user_id in users:
                    await self.send_digest_to_user(user_id)
                    
            except Exception as e:
                logging.error(f"Error sending digests: {e}")
            
            # Check every minute
            await asyncio.sleep(60)
    
    async def send_digest_to_user(self, user_id: int):
        """Send personalized digest to user"""
        try:
            interests = self.db.get_user_interests(user_id)
            
            if not interests:
                interests = ['tech', 'world', 'kyrgyzstan']  # Default interests
            
            digest = self.aggregator.generate_digest(interests, limit=10)
            
            await self.bot.send_message(
                user_id,
                digest,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            self.db.update_last_sent(user_id)
            logging.info(f"Digest sent to user {user_id}")
            
        except Exception as e:
            logging.error(f"Error sending digest to {user_id}: {e}")
    
    async def send_digest_now(self, user_id: int) -> str:
        """Send digest immediately (for /digest command)"""
        try:
            interests = self.db.get_user_interests(user_id)
            
            if not interests:
                return "❌ У вас нет выбранных интересов. Используйте /interests для настройки."
            
            digest = self.aggregator.generate_digest(interests, limit=10)
            
            await self.bot.send_message(
                user_id,
                digest,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            return "✅ Дайджест отправлен!"
            
        except Exception as e:
            logging.error(f"Error sending digest: {e}")
            return f"❌ Ошибка при отправке дайджеста: {e}"
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
        logging.info("News scheduler stopped")


async def run_scheduler_once(db):
    """Run news collection once (for manual trigger)"""
    aggregator = NewsAggregator(db)
    try:
        count = await aggregator.process_and_save_news()
        return count
    finally:
        await aggregator.close_session()
