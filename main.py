"""
Multi-platform bot entry point v2.6.0
Runs Telegram and WhatsApp bots simultaneously with webhook support for Railway.

Usage:
  python main.py              # Run bot on Railway (webhook mode)
  python main.py --polling    # Run locally with polling
  python main.py --diagnose   # Run diagnostics
"""
import logging
import asyncio
import sys
import os
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiogram import types

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
USE_POLLING = len(sys.argv) > 1 and sys.argv[1] == '--polling'


async def main():
    """Main entry point - starts both bots with webhook support on Railway."""
    logger.info("=" * 70)
    logger.info("🚀 Starting Multi-Platform Bot v2.6.0")
    logger.info("Platforms: Telegram + WhatsApp (with webhooks)")
    logger.info(f"Environment: {'Railway' if IS_RAILWAY else 'Local'}")
    logger.info(f"Mode: {'POLLING (local)' if USE_POLLING else 'WEBHOOK (production)'}")
    logger.info("=" * 70)

    # Create aiohttp app for webhook support
    app = web.Application()
    telegram_bot = None
    whatsapp_bot = None

    if IS_RAILWAY and not USE_POLLING:
        # ===== RAILWAY MODE (webhook) =====
        from adapters.telegram_full import FullTelegramBot
        from adapters.whatsapp_webhook import WhatsAppWebhookBot

        # Initialize Telegram bot
        telegram_bot = FullTelegramBot()
        
        if telegram_bot and telegram_bot.enabled:
            # Create webhook handler for Telegram
            async def telegram_webhook_handler(request: Request) -> Response:
                try:
                    body = await request.json()
                    update = types.Update(**body)
                    await telegram_bot.dp.feed_update(telegram_bot.bot, update)
                    return web.Response(status=200)
                except Exception as e:
                    logger.error(f"Telegram webhook error: {e}")
                    return web.Response(status=500, text=f"Error: {e}")
            
            app.router.add_post('/webhook-telegram', telegram_webhook_handler)
            logger.info("✅ Telegram webhook handler added: /webhook-telegram")

        # Initialize WhatsApp bot
        whatsapp_bot = WhatsAppWebhookBot()
        if whatsapp_bot and whatsapp_bot.enabled:
            whatsapp_bot.setup_routes(app)
            logger.info("✅ WhatsApp webhook handler added: /webhook-whatsapp")

        # Setup aiohttp server
        runner = web.AppRunner(app)
        await runner.setup()

        # Get port from Railway
        port = int(os.environ.get('PORT', 8080))
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()

        logger.info(f"🌐 Webhook server started on port {port}")

        # Set webhooks
        webhook_host = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
        if webhook_host:
            # Set Telegram webhook
            if telegram_bot and telegram_bot.enabled:
                telegram_webhook_url = f"https://{webhook_host}/webhook-telegram"
                await telegram_bot.bot.set_webhook(telegram_webhook_url)
                logger.info(f"✅ Telegram webhook SET: {telegram_webhook_url}")

            logger.info(f"📱 WhatsApp webhook URL: https://{webhook_host}/webhook-whatsapp")
            logger.info(f"🤖 Telegram webhook URL: https://{webhook_host}/webhook-telegram")
        else:
            logger.warning("⚠️  RAILWAY_PUBLIC_DOMAIN not set!")

        # Keep server running
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger.info("Shutdown requested")
        finally:
            await runner.cleanup()
            if telegram_bot:
                try:
                    await telegram_bot.bot.delete_webhook()
                except:
                    pass

    else:
        # ===== LOCAL MODE (polling) =====
        from adapters.telegram_full import run_full_telegram_bot
        from adapters.whatsapp_bot import run_whatsapp_bot
        import threading

        logger.info("🏃 Running in POLLING mode (for local development)")

        # Run WhatsApp bot in separate thread
        whatsapp_thread = threading.Thread(target=run_whatsapp_bot, daemon=True)
        whatsapp_thread.start()
        logger.info("✅ WhatsApp bot started (polling mode)")

        # Run Telegram bot in main thread
        await run_full_telegram_bot()


if __name__ == "__main__":
    # Check for diagnose argument
    if len(sys.argv) > 1 and sys.argv[1] == '--diagnose':
        print("🔍 Запуск диагностики...")
        import subprocess
        subprocess.run([sys.executable, 'diagnose_whatsapp_webhook.py'])
        sys.exit(0)

    # Safety check - only run on Railway or explicitly allowed
    if not IS_RAILWAY and not USE_POLLING and os.environ.get('ALLOW_LOCAL_RUN') != 'true':
        logger.warning("=" * 70)
        logger.warning("⚠️  Bot is NOT running locally!")
        logger.warning("This bot is designed to run on Railway.")
        logger.warning("To run locally, use: python main.py --polling")
        logger.warning("=" * 70)
        print("\n[STOP] Bot stopped locally. Deploy to Railway to run.")
        print("       Or use 'python main.py --polling' to test locally.\n")
        print("       To diagnose WhatsApp config: python main.py --diagnose")
        sys.exit(0)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
        sys.exit(0)
