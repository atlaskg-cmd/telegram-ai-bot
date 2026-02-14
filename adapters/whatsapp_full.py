"""
Full-featured WhatsApp Bot Adapter using Green API.
Includes extended functionality adapted for WhatsApp text interface.
Documentation: https://green-api.com/docs/
"""
import logging
import os
import time
import requests
import asyncio
from threading import Thread
from datetime import datetime

# Import core modules
from core.converter import convert_cny_to_kgs, convert_kgs_to_cny, format_conversion_result, get_currency
from database import Database
from news_aggregator import NewsAggregator
from crypto_tracker import crypto

logger = logging.getLogger(__name__)

# Enable debug logging for WhatsApp
logging.basicConfig(level=logging.DEBUG)


class FullWhatsAppBot:
    """
    Full-featured WhatsApp bot using Green API.
    Text-based interface optimized for WhatsApp.
    """
    
    def __init__(self):
        self.api_url = "https://api.green-api.com"
        self.id_instance = os.environ.get("GREEN_API_ID")
        self.api_token = os.environ.get("GREEN_API_TOKEN")
        
        # User states for multi-step interactions
        self.user_states = {}
        self.user_contexts = {}  # Store context like last command
        
        # Initialize services
        if self.id_instance and self.api_token:
            self.enabled = True
            self.db = Database()
            self.news_agg = NewsAggregator(self.db)
            logger.info(f"Full WhatsApp bot initialized (ID: {self.id_instance[:5]}...)")
        else:
            logger.warning("Green API credentials not set! WhatsApp bot disabled.")
            self.enabled = False
    
    def send_message(self, chat_id, message):
        """Send text message to WhatsApp user."""
        if not self.enabled:
            return False
        
        url = f"{self.api_url}/waInstance{self.id_instance}/SendMessage/{self.api_token}"
        payload = {
            "chatId": chat_id,
            "message": message
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                logger.info(f"WhatsApp message sent to {chat_id}")
                return True
            else:
                logger.error(f"Failed to send WhatsApp message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False
    
    def send_menu(self, chat_id):
        """Send main menu."""
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
        self.send_message(chat_id, menu_text)
    
    def handle_message(self, message_data):
        """Process incoming WhatsApp message."""
        try:
            logger.debug(f"Received message data: {message_data}")
            
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
            
            if not sender:
                logger.warning("No sender in message data")
                return
            
            if not text:
                logger.info(f"No text in message from {sender}, type: {message_type}")
                return
            
            user_id = sender
            text = text.strip()
            text_lower = text.lower()
            
            logger.info(f"✅ PROCESSING: WhatsApp message from {user_id} ({sender_name}): '{text}'")
            
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
                    self.send_message(sender, format_conversion_result(result))
                    self.send_message(sender, "💡 Отправьте *Меню* для возврата")
                    del self.user_states[user_id]
                    return
                
                elif state == "awaiting_kgs_amount":
                    result = convert_kgs_to_cny(text)
                    self.send_message(sender, format_conversion_result(result))
                    self.send_message(sender, "💡 Отправьте *Меню* для возврата")
                    del self.user_states[user_id]
                    return
            
            # Handle commands and menu items
            # Menu shortcuts
            if text_lower in ["/start", "привет", "hello", "hi", "меню", "menu", "0"]:
                self.send_menu(sender)
            
            # CNY to KGS
            elif any(x in text_lower for x in ["юань → сом", "юань в сом", "cny to kgs", "/cny_kgs", 
                                                 "1", "🇨🇳", "cny", "юань"]):
                self.user_states[user_id] = "awaiting_cny_amount"
                self.send_message(
                    sender,
                    "🇨🇳 *Юань → Сом*\n\nВведите сумму в юанях (CNY):"
                )
            
            # KGS to CNY
            elif any(x in text_lower for x in ["сом → юань", "сом в юань", "kgs to cny", "/kgs_cny",
                                                 "2", "🇰🇬", "kgs", "сом"]):
                self.user_states[user_id] = "awaiting_kgs_amount"
                self.send_message(
                    sender,
                    "🇰🇬 *Сом → Юань*\n\nВведите сумму в сомах (KGS):"
                )
            
            # Currency rates
            elif any(x in text_lower for x in ["💰 курс", "курс", "/currency", "usd", "доллар", "3"]):
                self.send_message(sender, get_currency())
                self.send_message(sender, "💡 Ещё команды: *Меню*")
            
            # News
            elif any(x in text_lower for x in ["📰 новости", "новости", "/news", "4"]):
                self._send_news(sender)
            
            # Digest
            elif any(x in text_lower for x in ["📰 дайджест", "дайджест", "/digest", "5"]):
                self._send_digest(sender)
            
            # Crypto
            elif any(x in text_lower for x in ["💰 криптовалюта", "криптовалюта", "крипто", 
                                                "/crypto", "btc", "bitcoin", "6"]):
                self._send_crypto(sender)
            
            # Portfolio
            elif any(x in text_lower for x in ["📈 портфель", "портфель", "/portfolio", "7"]):
                self._send_portfolio(sender, user_id)
            
            # Help
            elif any(x in text_lower for x in ["❓ помощь", "помощь", "/help", "help", "8"]):
                self._send_help(sender)
            
            # Quick number input (assume CNY if no state)
            elif text.replace(',', '').replace('.', '').isdigit() and float(text.replace(',', '.')) > 0:
                amount = float(text.replace(',', '.'))
                # Try to guess based on typical amounts
                if amount > 1000:
                    # Probably KGS
                    result = convert_kgs_to_cny(amount)
                    self.send_message(sender, format_conversion_result(result))
                else:
                    # Probably CNY
                    result = convert_cny_to_kgs(amount)
                    self.send_message(sender, format_conversion_result(result))
                self.send_message(sender, "💡 Отправьте *Меню* для других функций")
            
            else:
                # Unknown command
                self.send_message(
                    sender,
                    "❓ Не понял команду.\n\n"
                    "Отправьте *Меню* чтобы увидеть доступные команды."
                )
        
        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {e}")
    
    def _send_news(self, chat_id):
        """Send latest news."""
        try:
            news = self.news_agg.get_news_by_category("kyrgyzstan", limit=5)
            
            if not news:
                self.send_message(chat_id, "📰 Новости временно недоступны.")
                return
            
            text = "📰 *Последние новости Кыргызстана*\n\n"
            for i, item in enumerate(news[:5], 1):
                title = item.get('title', 'Без заголовка')
                text += f"{i}. {title}\n\n"
            
            text += "💡 Отправьте *Дайджест* для AI анализа"
            self.send_message(chat_id, text)
            
        except Exception as e:
            logger.error(f"News error: {e}")
            self.send_message(chat_id, "❌ Ошибка при получении новостей.")
    
    def _send_digest(self, chat_id):
        """Send AI digest."""
        try:
            self.send_message(chat_id, "⏳ Генерирую AI дайджест...")
            digest = self.news_agg.generate_digest("kyrgyzstan")
            
            if digest:
                # WhatsApp has 4096 char limit, split if needed
                if len(digest) > 4000:
                    parts = [digest[i:i+4000] for i in range(0, len(digest), 4000)]
                    for i, part in enumerate(parts):
                        header = f"📰 *AI Дайджест ({i+1}/{len(parts)})*\n\n" if len(parts) > 1 else "📰 *AI Дайджест*\n\n"
                        self.send_message(chat_id, header + part)
                        time.sleep(1)  # Rate limit
                else:
                    self.send_message(chat_id, f"📰 *AI Дайджест*\n\n{digest}")
            else:
                self.send_message(chat_id, "❌ Не удалось сгенерировать дайджест.")
                
        except Exception as e:
            logger.error(f"Digest error: {e}")
            self.send_message(chat_id, "❌ Ошибка при генерации дайджеста.")
    
    def _send_crypto(self, chat_id):
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
            self.send_message(chat_id, text)
            
        except Exception as e:
            logger.error(f"Crypto error: {e}")
            self.send_message(chat_id, "❌ Ошибка при получении данных.")
    
    def _send_portfolio(self, chat_id, user_id):
        """Send user's crypto portfolio."""
        try:
            portfolio = crypto.get_portfolio(user_id)
            
            if not portfolio:
                self.send_message(
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
            self.send_message(chat_id, text)
            
        except Exception as e:
            logger.error(f"Portfolio error: {e}")
            self.send_message(chat_id, "❌ Ошибка при получении портфеля.")
    
    def _send_help(self, chat_id):
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
        self.send_message(chat_id, help_text)
    
    def get_notifications(self):
        """Fetch new messages from Green API."""
        if not self.enabled:
            return
        
        url = f"{self.api_url}/waInstance{self.id_instance}/ReceiveNotification/{self.api_token}"
        
        try:
            response = requests.get(url, timeout=30)
            logger.debug(f"ReceiveNotification status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data:
                    logger.info(f"📨 Received notification: {data.get('body', {}).get('typeWebhook', 'unknown')}")
                
                if data and data.get("receiptId"):
                    receipt_id = data["receiptId"]
                    webhook_type = data.get("body", {}).get("typeWebhook", "unknown")
                    logger.debug(f"Received notification: type={webhook_type}, receiptId={receipt_id}")
                    
                    # Process message
                    body = data.get("body", {})
                    if body.get("typeWebhook") == "incomingMessageReceived":
                        logger.info(f"Processing incoming message notification")
                        self.handle_message(body)
                    elif body.get("typeWebhook") == "outgoingMessageStatus":
                        logger.debug(f"Outgoing message status: {body}")
                    elif body.get("typeWebhook") == "stateInstanceChanged":
                        logger.info(f"Instance state changed: {body}")
                    
                    # Delete notification after processing
                    delete_url = f"{self.api_url}/waInstance{self.id_instance}/DeleteNotification/{self.api_token}/{receipt_id}"
                    delete_response = requests.delete(delete_url, timeout=10)
                    if delete_response.status_code == 200:
                        logger.debug(f"Notification {receipt_id} deleted successfully")
                    else:
                        logger.warning(f"Failed to delete notification {receipt_id}: {delete_response.status_code}")
                else:
                    # No new notifications - this is normal
                    pass
            else:
                logger.error(f"ReceiveNotification failed: HTTP {response.status_code}")
        
        except requests.exceptions.Timeout:
            # Timeout is normal for long polling
            pass
        except Exception as e:
            logger.error(f"Error fetching WhatsApp notifications: {e}")
    
    def run(self):
        """Main loop for WhatsApp bot."""
        if not self.enabled:
            logger.error("❌ WhatsApp bot is disabled (no credentials)")
            return
        
        logger.info("🚀 Full WhatsApp bot started!")
        logger.info(f"   Instance ID: {self.id_instance[:8]}...")
        logger.info(f"   API URL: {self.api_url}")
        
        loop_count = 0
        while True:
            try:
                loop_count += 1
                if loop_count % 12 == 0:  # Log every minute
                    logger.debug(f"WhatsApp polling... (iteration {loop_count})")
                
                self.get_notifications()
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"❌ WhatsApp bot error: {e}")
                time.sleep(10)


def run_full_whatsapp_bot():
    """Entry point for running full WhatsApp bot."""
    bot = FullWhatsAppBot()
    if bot.enabled:
        bot.run()
    else:
        logger.warning("Full WhatsApp bot not started - credentials missing")
