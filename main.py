"""
Multi-platform bot entry point.
Runs Telegram and WhatsApp bots simultaneously using shared core logic.
"""
import logging
import asyncio
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Import adapters
from adapters.telegram_bot import run_telegram_bot
from adapters.whatsapp_bot import run_whatsapp_bot
from threading import Thread


def run_whatsapp_in_thread():
    """Run WhatsApp bot in separate thread (it's synchronous)."""
    try:
        run_whatsapp_bot()
    except Exception as e:
        logger.error(f"WhatsApp bot thread error: {e}")


async def main():
    """Main entry point - starts both bots."""
    logger.info("=" * 60)
    logger.info("🚀 Starting Multi-Platform Bot")
    logger.info("Platforms: Telegram + WhatsApp")
    logger.info("=" * 60)
    
    tasks = []
    
    # Start WhatsApp bot in background thread
    whatsapp_thread = Thread(target=run_whatsapp_in_thread, daemon=True)
    whatsapp_thread.start()
    logger.info("WhatsApp bot thread started")
    
    # Start Telegram bot (async, in main thread)
    tasks.append(run_telegram_bot())
    
    # Run all tasks
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Main loop error: {e}")
    
    logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Goodbye!")
        sys.exit(0)
