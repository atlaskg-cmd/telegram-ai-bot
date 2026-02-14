"""
WhatsApp Bot Adapter using Green API.
Documentation: https://green-api.com/docs/
"""
import logging
import os
import time
import requests
from threading import Thread
from core.converter import convert_cny_to_kgs, convert_kgs_to_cny, format_conversion_result

logger = logging.getLogger(__name__)


class WhatsAppBot:
    """
    WhatsApp bot using Green API.
    Requires GREEN_API_ID and GREEN_API_TOKEN environment variables.
    """
    
    def __init__(self):
        self.api_url = "https://api.green-api.com"
        self.id_instance = os.environ.get("GREEN_API_ID")
        self.api_token = os.environ.get("GREEN_API_TOKEN")
        
        # User states for multi-step interactions
        self.user_states = {}
        
        if not self.id_instance or not self.api_token:
            logger.warning("Green API credentials not set! WhatsApp bot will not work.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"WhatsApp bot initialized (ID: {self.id_instance[:5]}...)")
    
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
        """Send main menu with buttons (if supported) or text."""
        menu_text = (
            "🤖 *Привет! Я бот-конвертер валют*\n\n"
            "Выберите действие:\n\n"
            "🇨🇳 *Юань → Сом* - конвертировать CNY в KGS\n"
            "🇰🇬 *Сом → Юань* - конвертировать KGS в CNY\n"
            "💰 *Курс* - текущий курс USD\n"
            "❓ *Помощь* - справка\n\n"
            "Отправьте команду или напишите сумму для конвертации."
        )
        self.send_message(chat_id, menu_text)
    
    def handle_message(self, message_data):
        """Process incoming WhatsApp message."""
        try:
            # Extract message info
            sender = message_data.get("senderData", {}).get("sender")
            message_text = message_data.get("messageData", {}).get("textMessageData", {}).get("textMessage", "")
            
            if not sender or not message_text:
                return
            
            user_id = sender  # phone number as user id
            text = message_text.strip()
            
            logger.info(f"WhatsApp message from {user_id}: {text}")
            
            # Check if user has pending state
            if user_id in self.user_states:
                state = self.user_states[user_id]
                
                if state == "awaiting_cny_amount":
                    result = convert_cny_to_kgs(text)
                    self.send_message(sender, format_conversion_result(result))
                    del self.user_states[user_id]
                    return
                
                elif state == "awaiting_kgs_amount":
                    result = convert_kgs_to_cny(text)
                    self.send_message(sender, format_conversion_result(result))
                    del self.user_states[user_id]
                    return
            
            # Handle commands
            text_lower = text.lower()
            
            if text_lower in ["/start", "привет", "hello", "hi", "меню", "menu"]:
                self.send_menu(sender)
            
            elif text_lower in ["🇨🇳 юань → сом", "юань в сом", "cny to kgs", "/cny_kgs", "юань", "cny"]:
                self.user_states[user_id] = "awaiting_cny_amount"
                self.send_message(
                    sender,
                    "🇨🇳 *Юань → Сом*\n\n"
                    "Введите сумму в юанях (CNY):"
                )
            
            elif text_lower in ["🇰🇬 сом → юань", "сом в юань", "kgs to cny", "/kgs_cny", "сом", "kgs"]:
                self.user_states[user_id] = "awaiting_kgs_amount"
                self.send_message(
                    sender,
                    "🇰🇬 *Сом → Юань*\n\n"
                    "Введите сумму в сомах (KGS):"
                )
            
            elif text_lower in ["💰 курс", "курс", "/currency", "usd", "доллар"]:
                from core.converter import get_currency
                self.send_message(sender, get_currency())
            
            elif text_lower in ["❓ помощь", "помощь", "/help", "help"]:
                help_text = (
                    "📖 *Справка*\n\n"
                    "*Команды:*\n"
                    "🇨🇳 Юань → Сом - конвертировать CNY в KGS\n"
                    "🇰🇬 Сом → Юань - конвертировать KGS в CNY\n"
                    "💰 Курс - курс USD\n\n"
                    "*Или просто отправьте число* после выбора направления конвертации."
                )
                self.send_message(sender, help_text)
            
            else:
                # Unknown command
                self.send_message(
                    sender,
                    "❓ Не понял команду.\n\n"
                    "Отправьте *Меню* чтобы увидеть доступные команды."
                )
        
        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {e}")
    
    def get_notifications(self):
        """Fetch new messages from Green API."""
        if not self.enabled:
            return
        
        url = f"{self.api_url}/waInstance{self.id_instance}/ReceiveNotification/{self.api_token}"
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                if data and data.get("receiptId"):
                    receipt_id = data["receiptId"]
                    
                    # Process message
                    body = data.get("body", {})
                    if body.get("typeWebhook") == "incomingMessageReceived":
                        self.handle_message(body)
                    
                    # Delete notification after processing
                    delete_url = f"{self.api_url}/waInstance{self.id_instance}/DeleteNotification/{self.api_token}/{receipt_id}"
                    requests.delete(delete_url, timeout=10)
        
        except Exception as e:
            logger.error(f"Error fetching WhatsApp notifications: {e}")
    
    def run(self):
        """Main loop for WhatsApp bot."""
        if not self.enabled:
            logger.info("WhatsApp bot is disabled (no credentials)")
            return
        
        logger.info("WhatsApp bot started!")
        
        while True:
            try:
                self.get_notifications()
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"WhatsApp bot error: {e}")
                time.sleep(10)


def run_whatsapp_bot():
    """Entry point for running WhatsApp bot in separate thread."""
    bot = WhatsAppBot()
    if bot.enabled:
        bot.run()
    else:
        logger.warning("WhatsApp bot not started - credentials missing")
