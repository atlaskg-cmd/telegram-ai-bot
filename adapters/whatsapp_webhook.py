"""
WhatsApp Bot Adapter using Green API with Webhook.
Replaces polling method with webhook for Railway deployment.
"""
import logging
import os
import json
from aiohttp import web
import asyncio
import aiohttp

# Import core modules
from core.converter import convert_cny_to_kgs, convert_kgs_to_cny, format_conversion_result, get_currency
from database import Database
from news_aggregator import NewsAggregator
from crypto_tracker import crypto

logger = logging.getLogger(__name__)


class WhatsAppWebhookBot:
    """
    WhatsApp bot using Green API with webhook method.
    Better suited for Railway deployment than polling.
    """

    def __init__(self):
        self.id_instance = os.environ.get("GREEN_API_ID")
        self.api_token = os.environ.get("GREEN_API_TOKEN")

        # User states for multi-step interactions
        self.user_states = {}
        self.user_contexts = {}

        # Initialize services
        if self.id_instance and self.api_token:
            self.enabled = True
            self.db = Database()
            self.news_agg = NewsAggregator(self.db)
            logger.info(f"WhatsApp Webhook bot initialized (ID: {self.id_instance[:5]}...)")
        else:
            logger.warning("Green API credentials not set! WhatsApp bot disabled.")
            self.enabled = False

    async def send_message(self, chat_id, message):
        """Send text message to WhatsApp user."""
        if not self.enabled:
            return False

        import aiohttp
        api_url = "https://api.green-api.com"
        url = f"{api_url}/waInstance{self.id_instance}/SendMessage/{self.api_token}"
        payload = {
            "chatId": chat_id,
            "message": message
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        logger.info(f"WhatsApp message sent to {chat_id}")
                        return True
                    else:
                        text = await response.text()
                        logger.error(f"Failed to send WhatsApp message: {text}")
                        return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False

    async def send_menu(self, chat_id):
        """Send main menu."""
        logger.info(f"Preparing to send menu to {chat_id}")
        menu_text = (
            "🤖 *Привет! Я AI бот-конвертер*\n\n"
            "*Выберите действие:*\n\n"
            "💱 *Конвертер:*\n"
            "🇨🇳 Юань → Сом\n"
            "🇰🇬 Сом → Юань\n"
            "💰 Курс USD\n\n"
            "📰 *Информация:*\n"
            "📰 Новости\n"
            "📰 Дайджест (AI)\n\n"
            "💰 *Криптовалюты:*\n"
            "💰 Крипто - курсы\n"
            "📈 Портфель\n\n"
            "❓ *Помощь* - справка\n\n"
            "_Отправьте номер пункта или текст команду_"
        )
        result = await self.send_message(chat_id, menu_text)
        logger.info(f"Menu sending result to {chat_id}: {result}")

    async def handle_message(self, message_data):
        """Process incoming WhatsApp message from webhook."""
        logger.info("handle_message function called")
        try:
            logger.debug(f"Received webhook message data: {message_data}")

            # Extract message info
            sender_data = message_data.get("senderData", {})
            sender = sender_data.get("sender")
            sender_name = sender_data.get("senderName", "Пользователь")

            message_info = message_data.get("messageData", {})
            message_type = message_info.get("typeMessage", "")

            logger.info(f"Message type: {message_type}, Sender: {sender}")

            # Get text message
            text = ""
            if message_type == "textMessage":
                text = message_info.get("textMessageData", {}).get("textMessage", "")
            elif message_type == "extendedTextMessage":
                text = message_info.get("extendedTextMessageData", {}).get("text", "")

            logger.info(f"Extracted text: '{text}'")

            if not sender:
                logger.warning("No sender in message data")
                return

            if not text:
                logger.info(f"No text in message from {sender}, type: {message_type}")
                return

            user_id = sender
            text = text.strip()
            text_lower = text.lower()

            logger.info(f"✅ PROCESSING: WhatsApp message from {user_id} ({sender_name}): '{text}' (lowercase: '{text_lower}')")

            # Register user in DB
            try:
                self.db.add_user(user_id, sender_name, sender_name, "")
            except:
                pass  # WhatsApp ID format may differ

            # Check user state first
            if user_id in self.user_states:
                state = self.user_states[user_id]

                if state == "awaiting_cny_amount":
                    result = convert_cny_to_kgs(text)
                    await self.send_message(sender, format_conversion_result(result))
                    await self.send_message(sender, "💡 Отправьте *Меню* для возврата")
                    del self.user_states[user_id]
                    return

                elif state == "awaiting_kgs_amount":
                    result = convert_kgs_to_cny(text)
                    await self.send_message(sender, format_conversion_result(result))
                    await self.send_message(sender, "💡 Отправьте *Меню* для возврата")
                    del self.user_states[user_id]
                    return

            # Handle commands and menu items
            # Menu shortcuts
            if text_lower in ["/start", "привет", "hello", "hi", "меню", "menu", "0"]:
                logger.info(f"Processing menu command for {sender}")
                await self.send_menu(sender)
                logger.info(f"Menu sent to {sender}")

            # CNY to KGS
            elif any(x in text_lower for x in ["юань → сом", "юань в сом", "cny to kgs", "/cny_kgs",
                                                 "1", "🇨🇳", "cny", "юань"]):
                self.user_states[user_id] = "awaiting_cny_amount"
                await self.send_message(
                    sender,
                    "🇨🇳 *Юань → Сом*\n\nВведите сумму в юанях (CNY):"
                )

            # KGS to CNY
            elif any(x in text_lower for x in ["сом → юань", "сом в юань", "kgs to cny", "/kgs_cny",
                                                 "2", "🇰🇬", "kgs", "сом"]):
                self.user_states[user_id] = "awaiting_kgs_amount"
                await self.send_message(
                    sender,
                    "🇰🇬 *Сом → Юань*\n\nВведите сумму в сомах (KGS):"
                )

            # Currency rates
            elif any(x in text_lower for x in ["💰 курс", "курс", "/currency", "usd", "доллар", "3"]):
                await self.send_message(sender, get_currency())
                await self.send_message(sender, "💡 Ещё команды: *Меню*")

            # News
            elif any(x in text_lower for x in ["📰 новости", "новости", "/news", "4"]):
                await self._send_news(sender)

            # Digest
            elif any(x in text_lower for x in ["📰 дайджест", "дайджест", "/digest", "5"]):
                await self._send_digest(sender)

            # Crypto
            elif any(x in text_lower for x in ["💰 криптовалюта", "крипто",
                                                "/crypto", "btc", "bitcoin", "6"]):
                await self._send_crypto(sender)

            # Portfolio
            elif any(x in text_lower for x in ["📈 портфель", "портфель", "/portfolio", "7"]):
                await self._send_portfolio(sender, user_id)

            # Help
            elif any(x in text_lower for x in ["❓ помощь", "помощь", "/help", "help", "8"]):
                await self._send_help(sender)

            # Quick number input (assume CNY if no state)
            elif text.replace(',', '').replace('.', '').isdigit() and float(text.replace(',', '.')) > 0:
                amount = float(text.replace(',', '.'))
                # Try to guess based on typical amounts
                if amount > 1000:
                    # Probably KGS
                    result = convert_kgs_to_cny(amount)
                    await self.send_message(sender, format_conversion_result(result))
                else:
                    # Probably CNY
                    result = convert_cny_to_kgs(amount)
                    await self.send_message(sender, format_conversion_result(result))
                await self.send_message(sender, "💡 Отправьте *Меню* для других функций")

            else:
                # Unknown command
                await self.send_message(
                    sender,
                    "❓ Не понял команду.\n\n"
                    "Отправьте *Меню* чтобы увидеть доступные команды."
                )

        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {e}")

    async def _send_news(self, chat_id):
        """Send latest news."""
        try:
            news = self.news_agg.get_news_by_category("kyrgyzstan", limit=5)

            if not news:
                await self.send_message(chat_id, "📰 Новости временно недоступны.")
                return

            text = "📰 *Последние новости Кыргызстана*\n\n"
            for i, item in enumerate(news[:5], 1):
                title = item.get('title', 'Без заголовка')
                text += f"{i}. {title}\n\n"

            text += "💡 Отправьте *Дайджест* для AI анализа"
            await self.send_message(chat_id, text)

        except Exception as e:
            logger.error(f"News error: {e}")
            await self.send_message(chat_id, "❌ Ошибка при получении новостей.")

    async def _send_digest(self, chat_id):
        """Send AI digest."""
        try:
            await self.send_message(chat_id, "⏳ Генерирую AI дайджест...")
            digest = self.news_agg.generate_digest("kyrgyzstan")

            if digest:
                # WhatsApp has 4096 char limit, split if needed
                if len(digest) > 4000:
                    parts = [digest[i:i+4000] for i in range(0, len(digest), 4000)]
                    for i, part in enumerate(parts):
                        header = f"📰 *AI Дайджест ({i+1}/{len(parts)})*\n\n" if len(parts) > 1 else "📰 *AI Дайджест*\n\n"
                        await self.send_message(chat_id, header + part)
                else:
                    await self.send_message(chat_id, f"📰 *AI Дайджест*\n\n{digest}")
            else:
                await self.send_message(chat_id, "❌ Не удалось сгенерировать дайджест.")

        except Exception as e:
            logger.error(f"Digest error: {e}")
            await self.send_message(chat_id, "❌ Ошибка при генерации дайджеста.")

    async def _send_crypto(self, chat_id):
        """Send crypto prices."""
        try:
            btc = crypto.get_price("bitcoin")
            eth = crypto.get_price("ethereum")

            text = "💰 *Криптовалюты*\n\n"

            if btc:
                price = btc.get('usd', 'N/A')
                change = btc.get('usd_24h_change', 0)
                emoji = "🟢" if change >= 0 else "🔴"
                text += f"*Bitcoin (BTC)*\n{emoji} ${price:,.2f} ({change:+.2f}%)\n\n"

            if eth:
                price = eth.get('usd', 'N/A')
                change = eth.get('usd_24h_change', 0)
                emoji = "🟢" if change >= 0 else "🔴"
                text += f"*Ethereum (ETH)*\n{emoji} ${price:,.2f} ({change:+.2f}%)\n\n"

            text += "💡 Отправьте *Портфель* для ваших криптовалют"
            await self.send_message(chat_id, text)

        except Exception as e:
            logger.error(f"Crypto error: {e}")
            await self.send_message(chat_id, "❌ Ошибка при получении данных.")

    async def _send_portfolio(self, chat_id, user_id):
        """Send user's crypto portfolio."""
        try:
            portfolio = crypto.get_portfolio(user_id)

            if not portfolio:
                await self.send_message(
                    chat_id,
                    "📈 *Ваш портфель пуст*\n\n"
                    "Добавьте криптовалюты через Telegram бота.\n"
                    "WhatsApp версия поддерживает только просмотр."
                )
                return

            text = "📈 *Мой крипто-портфель*\n\n"
            total_value = 0

            for item in portfolio:
                coin_id = item.get('coin_id')
                amount = item.get('amount', 0)
                price_data = crypto.get_price(coin_id)

                if price_data:
                    price = price_data.get('usd', 0)
                    value = amount * price
                    total_value += value
                    change_24h = price_data.get('usd_24h_change', 0)
                    emoji = "🟢" if change_24h >= 0 else "🔴"

                    text += f"{emoji} *{coin_id.upper()}*: {amount} = ${value:,.2f}\n"

            text += f"\n💰 *Итого: ${total_value:,.2f}*"
            await self.send_message(chat_id, text)

        except Exception as e:
            logger.error(f"Portfolio error: {e}")
            await self.send_message(chat_id, "❌ Ошибка при получении портфеля.")

    async def _send_help(self, chat_id):
        """Send help text."""
        help_text = (
            "📖 *Справка по командам*\n\n"
            "*Конвертер валют:*\n"
            "🇨🇳 Юань → Сом - конвертировать CNY\n"
            "🇰🇬 Сом → Юань - конвертировать KGS\n"
            "💰 Курс - курс USD\n\n"
            "*Информация:*\n"
            "📰 Новости - последние новости\n"
            "📰 Дайджест - AI анализ новостей\n\n"
            "*Криптовалюты:*\n"
            "💰 Крипто - текущие курсы\n"
            "📈 Портфель - ваши криптовалюты\n\n"
            "*Или просто отправьте число* для быстрой конвертации:\n"
            "• До 1000 → считаем как Юани (CNY)\n"
            "• Больше 1000 → считаем как Сомы (KGS)"
        )
        await self.send_message(chat_id, help_text)

    async def webhook_handler(self, request):
        """Handle incoming webhook requests from Green API."""
        if not self.enabled:
            return web.Response(status=400, text="Bot disabled")

        try:
            data = await request.json()
            logger.info(f"Webhook received: {data}")

            # Process message - Green API sends data without "body" wrapper
            typeWebhook = data.get("typeWebhook")
            
            if typeWebhook == "incomingMessageReceived":
                logger.info("Processing incoming message from webhook")
                await self.handle_message(data)
            elif typeWebhook == "outgoingMessageStatus":
                logger.debug(f"Outgoing message status: {data}")
            elif typeWebhook == "stateInstanceChanged":
                logger.info(f"Instance state changed: {data}")

            # Return success response to Green API
            return web.Response(status=200, text="OK")

        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            return web.Response(status=500, text="Error")

    def setup_routes(self, app):
        """Setup webhook route for aiohttp app."""
        app.router.add_post('/webhook-whatsapp', self.webhook_handler)


def run_whatsapp_webhook_bot(app):
    """Setup WhatsApp webhook bot routes in main aiohttp app."""
    bot = WhatsAppWebhookBot()
    if bot.enabled:
        bot.setup_routes(app)
        logger.info("WhatsApp Webhook bot routes added")
        return bot
    else:
        logger.warning("WhatsApp Webhook bot not added - credentials missing")
        return None