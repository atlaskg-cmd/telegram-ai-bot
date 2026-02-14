"""
Multi-platform bot entry point v2.5.0
Runs Telegram and WhatsApp bots simultaneously using shared core logic.
Now with webhook support for WhatsApp on Railway.

Usage:
  python main.py              # Run bot normally
  python main.py --diagnose   # Run diagnostics
"""
import logging
import asyncio
import sys
import os
from aiohttp import web

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
    # On Railway - use full-featured bot with webhook support
    from adapters.telegram_full import run_full_telegram_bot
    from adapters.whatsapp_webhook import run_whatsapp_webhook_bot
    TELEGRAM_RUNNER = run_full_telegram_bot
    logger.info("Using FULL bot adapters with WhatsApp webhook (Railway mode)")
else:
    # Locally - use basic bot (or don't run at all)
    from adapters.telegram_bot import run_telegram_bot
    from adapters.whatsapp_bot import run_whatsapp_bot
    TELEGRAM_RUNNER = run_telegram_bot
    logger.info("Using BASIC bot adapters (Local mode)")


async def main():
    """Main entry point - starts both bots with webhook support."""
    logger.info("=" * 60)
    logger.info("🚀 Starting Multi-Platform Bot v2.5.0")
    logger.info("Platforms: Telegram + WhatsApp (with webhook)")
    logger.info(f"Environment: {'Railway' if IS_RAILWAY else 'Local'}")
    logger.info("=" * 60)

    # Create aiohttp app for webhook support
    app = web.Application()
    
    # Setup WhatsApp webhook if enabled
    whatsapp_bot = None
    if IS_RAILWAY:
        whatsapp_bot = run_whatsapp_webhook_bot(app)
    
    # Start Telegram bot
    telegram_task = asyncio.create_task(TELEGRAM_RUNNER())
    
    # Setup aiohttp server for webhooks
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Determine port (Railway provides PORT environment variable)
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Webhook server started on port {port}")
    if IS_RAILWAY and whatsapp_bot:
        logger.info("WhatsApp bot webhook is ready to receive messages")
        logger.info(f"Webhook URL should be: https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN')}/webhook-whatsapp")
    
    # Run all tasks
    try:
        await telegram_task
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Main loop error: {e}")
    finally:
        await runner.cleanup()

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
