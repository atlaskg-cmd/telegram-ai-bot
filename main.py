"""
Multi-platform bot entry point v2.5.0
Runs Telegram and WhatsApp bots simultaneously using shared core logic.

Usage:
  python main.py              # Run bot normally
  python main.py --diagnose   # Run diagnostics
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

# Check environment
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

# Import adapters
if IS_RAILWAY:
    # On Railway - use full-featured bot
    from adapters.telegram_full import run_full_telegram_bot
    from adapters.whatsapp_full import run_full_whatsapp_bot
    TELEGRAM_RUNNER = run_full_telegram_bot
    WHATSAPP_RUNNER = run_full_whatsapp_bot
    logger.info("Using FULL bot adapters (Railway mode)")
else:
    # Locally - use basic bot (or don't run at all)
    from adapters.telegram_bot import run_telegram_bot
    from adapters.whatsapp_bot import run_whatsapp_bot
    TELEGRAM_RUNNER = run_telegram_bot
    WHATSAPP_RUNNER = run_whatsapp_bot
    logger.info("Using BASIC bot adapters (Local mode)")

from threading import Thread


def run_whatsapp_in_thread():
    """Run WhatsApp bot in separate thread (it's synchronous)."""
    try:
        WHATSAPP_RUNNER()
    except Exception as e:
        logger.error(f"WhatsApp bot thread error: {e}")


async def main():
    """Main entry point - starts both bots."""
    logger.info("=" * 60)
    logger.info("🚀 Starting Multi-Platform Bot v2.5.0")
    logger.info("Platforms: Telegram + WhatsApp")
    logger.info(f"Environment: {'Railway' if IS_RAILWAY else 'Local'}")
    logger.info("=" * 60)
    
    tasks = []
    
    # Start WhatsApp bot in background thread
    whatsapp_thread = Thread(target=run_whatsapp_in_thread, daemon=True)
    whatsapp_thread.start()
    logger.info("WhatsApp bot thread started")
    
    # Start Telegram bot (async, in main thread)
    tasks.append(TELEGRAM_RUNNER())
    
    # Run all tasks
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Main loop error: {e}")
    
    logger.info("Bot stopped")


if __name__ == "__main__":
    # Check for diagnose argument
    if len(sys.argv) > 1 and sys.argv[1] == '--diagnose':
        print("🔍 Запуск диагностики...")
        import subprocess
        subprocess.run([sys.executable, 'diagnose_whatsapp.py'])
        sys.exit(0)
    
    # Safety check - only run on Railway or explicitly allowed
    if not IS_RAILWAY and os.environ.get('ALLOW_LOCAL_RUN') != 'true':
        logger.warning("=" * 60)
        logger.warning("⚠️  Bot is NOT running locally!")
        logger.warning("This bot is designed to run on Railway.")
        logger.warning("To run locally, set ALLOW_LOCAL_RUN=true")
        logger.warning("=" * 60)
        print("\n[STOP] Bot stopped locally. Deploy to Railway to run.")
        print("       Or set ALLOW_LOCAL_RUN=true to test locally.\n")
        print("       To diagnose WhatsApp config: python main.py --diagnose")
        sys.exit(0)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Goodbye!")
        sys.exit(0)
