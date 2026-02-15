"""
Full-featured Telegram Bot Adapter.
Includes all functionality from bot.py refactored for multi-platform architecture.
"""
import logging
import os
import sys
import asyncio
import tempfile
import re
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    Message, BufferedInputFile, FSInputFile, ReplyKeyboardMarkup, 
    KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.enums import ParseMode

# Import core modules
from core.converter import convert_cny_to_kgs, convert_kgs_to_cny, format_conversion_result, get_currency
from database import Database
from news_scheduler import NewsScheduler, run_scheduler_once
from news_aggregator import NewsAggregator
from image_generator import ImageGenerator, DeepSeekChat
from crypto_tracker import crypto

# Optional imports
try:
    from gtts import gTTS
    import io
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

logger = logging.getLogger(__name__)


def clean_text_for_tts(text):
    """Remove emojis and special characters for TTS."""
    text = re.sub(r'[^\w\s]', '', text)
    return text


class FullTelegramBot:
    """Full-featured Telegram bot with all capabilities."""
    
    def __init__(self):
        self.api_token = os.environ.get("TELEGRAM_API_TOKEN")
        if not self.api_token:
            logger.error("TELEGRAM_API_TOKEN not set!")
            self.enabled = False
            return
        
        self.bot = Bot(token=self.api_token)
        self.dp = Dispatcher()
        self.enabled = True
        
        # Load config
        self.config = self._load_config()
        
        # Initialize services
        self.db = Database()
        self.image_gen = ImageGenerator()
        self.deepseek_chat = DeepSeekChat()
        self.news_agg = NewsAggregator(self.db)
        
        # API keys
        self.OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or self.config.get("openrouter_api_key", "")
        self.WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", self.config.get("weather_api_key", ""))
        self.OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
        
        # Admin config
        self.ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
        
        # User states
        self.user_states = {}
        self.admin_states = {}
        self.voice_enabled = {}
        
        # Setup handlers
        self._setup_handlers()
        
        logger.info("Full Telegram bot initialized")
    
    def _load_config(self):
        """Load config from file."""
        import json
        config = {}
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            logger.warning('config.json not found, using defaults')
        except json.JSONDecodeError as e:
            logger.error(f'Invalid config.json: {e}')
        return config
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        if user_id == self.ADMIN_ID:
            return True
        return self.db.is_admin(user_id)
    
    def is_banned(self, user_id: int) -> bool:
        """Check if user is banned."""
        return self.db.is_banned(user_id) is not None
    
    async def check_banned(self, message: Message) -> bool:
        """Check and notify if user is banned."""
        ban_info = self.db.is_banned(message.from_user.id)
        if ban_info:
            await message.reply(
                f"⛔ <b>Вы заблокированы</b>\n\n"
                f"Причина: {ban_info.get('reason', 'Не указана')}\n"
                f"Дата блокировки: {ban_info.get('banned_at', 'Неизвестно')[:10]}",
                parse_mode=ParseMode.HTML
            )
            return True
        return False
    
    def _setup_handlers(self):
        """Register all message handlers."""
        
        # ===== MAIN KEYBOARD =====
        def get_main_keyboard(user_id: int = None):
            """Get main keyboard with all buttons."""
            keyboard = [
                [KeyboardButton(text="🌤 Погода Бишкек"), KeyboardButton(text="🌤 Погода Москва")],
                [KeyboardButton(text="💰 Курс валют"), KeyboardButton(text="📰 Новости")],
                [KeyboardButton(text="🇨🇳 Юань → Сом"), KeyboardButton(text="🇰🇬 Сом → Юань")],
                [KeyboardButton(text="📇 Контакты"), KeyboardButton(text="📰 AI Дайджест")],
                [KeyboardButton(text="🤖 AI Чат"), KeyboardButton(text="🎨 Сгенерировать картинку")],
                [KeyboardButton(text="💰 Криптовалюта"), KeyboardButton(text="📈 Мой портфель")],
            ]
            
            # Add admin or help button
            if user_id and self.is_admin(user_id):
                keyboard.append([KeyboardButton(text="👤 Админ")])
            else:
                keyboard.append([KeyboardButton(text="❓ Помощь")])
            
            return ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                one_time_keyboard=False
            )
        
        # ===== START & HELP =====
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            if await self.check_banned(message):
                return
            
            user = message.from_user
            welcome_text = (
                f"👋 <b>Привет, {user.first_name}!</b>\n\n"
                f"🤖 Я AI бот с множеством функций:\n\n"
                f"🌤 <b>Погода</b> - Бишкек, Москва, Иссык-Куль\n"
                f"💱 <b>Валюты</b> - USD, CNY ↔ KGS\n"
                f"📰 <b>Новости</b> - AI дайджест\n"
                f"🎨 <b>Картинки</b> - Генерация изображений\n"
                f"🤖 <b>AI Чат</b> - Умный ассистент\n"
                f"💰 <b>Крипто</b> - Отслеживание криптовалют\n\n"
                f"Выберите действие в меню ниже 👇"
            )
            await message.reply(welcome_text, parse_mode=ParseMode.HTML, reply_markup=get_main_keyboard(user.id))
            
            # Register user in DB
            self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            help_text = (
                "📖 <b>Справка по командам</b>\n\n"
                "<b>Основные:</b>\n"
                "/start - Начать работу\n"
                "/help - Эта справка\n\n"
                "<b>Погода:</b>\n"
                "🌤 Погода [город]\n\n"
                "<b>Валюты:</b>\n"
                "💰 Курс валют - USD, RUB\n"
                "🇨🇳 Юань → Сом - конвертация CNY\n"
                "🇰🇬 Сом → Юань - конвертация в CNY\n\n"
                "<b>AI:</b>\n"
                "/gpt4 [вопрос] - AI ассистент\n"
                "/image [описание] - Генерация картинки\n\n"
                "<b>Новости:</b>\n"
                "📰 Новости - Последние новости\n"
                "/digest - AI дайджест\n\n"
                "<b>Крипто:</b>\n"
                "💰 Криптовалюта - Курсы крипто\n"
                "📈 Мой портфель - Управление портфелем"
            )
            await message.reply(help_text, parse_mode=ParseMode.HTML)
        
        # ===== WEATHER =====
        async def get_weather(city: str, city_display: str = None):
            """Get weather for city."""
            if not self.WEATHER_API_KEY:
                return "❌ WEATHER_API_KEY не настроен"
            
            if city_display is None:
                city_display = city
            
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.WEATHER_API_KEY}&units=metric&lang=ru"
            
            try:
                import requests
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if data.get("cod") != 200:
                    return f"❌ Ошибка: {data.get('message', 'Город не найден')}"
                
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                desc = data["weather"][0]["description"]
                wind = data["wind"]["speed"]
                
                return (
                    f"🌤 <b>Погода в {city_display}</b>\n\n"
                    f"🌡 Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                    f"💧 Влажность: {humidity}%\n"
                    f"💨 Ветер: {wind} м/с\n"
                    f"☁️ {desc.capitalize()}"
                )
            except Exception as e:
                logger.error(f"Weather error: {e}")
                return "❌ Ошибка при получении погоды"
        
        @self.dp.message(lambda msg: msg.text and "Погода Бишкек" in msg.text)
        async def weather_bishkek(message: Message):
            if await self.check_banned(message):
                return
            weather = await get_weather("Bishkek", "Бишкек")
            await message.reply(weather, parse_mode=ParseMode.HTML)
        
        @self.dp.message(lambda msg: msg.text and "Погода Москва" in msg.text)
        async def weather_moscow(message: Message):
            if await self.check_banned(message):
                return
            weather = await get_weather("Moscow", "Москва")
            await message.reply(weather, parse_mode=ParseMode.HTML)
        
        # ===== CURRENCY =====
        @self.dp.message(lambda msg: msg.text and "Курс валют" in msg.text)
        async def btn_currency(message: Message):
            if await self.check_banned(message):
                return
            await message.reply(get_currency())
        
        @self.dp.message(lambda msg: msg.text and "Юань → Сом" in msg.text)
        async def btn_cny_to_kgs(message: Message):
            if await self.check_banned(message):
                return
            user_id = message.from_user.id
            self.user_states[user_id] = "awaiting_cny_amount"
            await message.reply(
                "🇨🇳 <b>Юань → Сом</b>\n\nВведите сумму в юанях (CNY):",
                parse_mode=ParseMode.HTML
            )
        
        @self.dp.message(lambda msg: msg.text and "Сом → Юань" in msg.text)
        async def btn_kgs_to_cny(message: Message):
            if await self.check_banned(message):
                return
            user_id = message.from_user.id
            self.user_states[user_id] = "awaiting_kgs_amount"
            await message.reply(
                "🇰🇬 <b>Сом → Юань</b>\n\nВведите сумму в сомах (KGS):",
                parse_mode=ParseMode.HTML
            )
        
        # ===== AI CHAT (DeepSeek) =====
        @self.dp.message(Command("gpt4"))
        async def deepseek_chat_handler(message: Message):
            if await self.check_banned(message):
                return
            
            user_id = message.from_user.id
            prompt = message.text.replace("/gpt4", "").strip()
            
            if not prompt:
                await message.reply(
                    "🤖 <b>AI Chat</b>\n\n"
                    "Использование: <code>/gpt4 ваш вопрос</code>\n\n"
                    "Например: <code>/gpt4 объясни квантовую физику простыми словами</code>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Check if user has chat history
            history = self.db.get_chat_history(user_id, limit=10)
            
            # Show typing
            await self.bot.send_chat_action(message.chat.id, "typing")
            
            try:
                # Use DeepSeek R1
                response = await self.deepseek_chat.chat(prompt, history)
                
                if response:
                    # Save to history
                    self.db.add_chat_message(user_id, "user", prompt)
                    self.db.add_chat_message(user_id, "assistant", response)
                    
                    # Send response (split if too long)
                    if len(response) > 4000:
                        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
                        for part in parts:
                            await message.reply(part)
                    else:
                        await message.reply(response)
                else:
                    await message.reply("❌ Не удалось получить ответ от AI. Попробуйте позже.")
                    
            except Exception as e:
                logger.error(f"DeepSeek error: {e}")
                await message.reply("❌ Ошибка при обработке запроса. Попробуйте позже.")
        
        @self.dp.message(lambda msg: msg.text and "AI Чат" in msg.text)
        async def btn_ai_chat(message: Message):
            if await self.check_banned(message):
                return
            await message.reply(
                "🤖 <b>AI Chat</b>\n\n"
                "Отправьте ваш вопрос с командой <code>/gpt4</code>\n\n"
                "Например: <code>/gpt4 как приготовить плов?</code>",
                parse_mode=ParseMode.HTML
            )
        
        # ===== IMAGE GENERATION =====
        @self.dp.message(Command("image"))
        async def generate_image_handler(message: Message):
            if await self.check_banned(message):
                return
            
            prompt = message.text.replace("/image", "").strip()
            
            if not prompt:
                await message.reply(
                    "🎨 <b>Генерация изображений</b>\n\n"
                    "Использование: <code>/image описание картинки</code>\n\n"
                    "Например: <code>/image кот в космосе, цифровое искусство</code>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Show uploading photo action
            await self.bot.send_chat_action(message.chat.id, "upload_photo")
            
            processing_msg = await message.reply("🎨 Генерирую изображение... Это может занять 10-30 секунд.")
            
            try:
                import asyncio
                image_data = await asyncio.wait_for(
                    asyncio.to_thread(self.image_gen.generate_image, prompt),
                    timeout=60.0
                )
                
                if image_data:
                    await processing_msg.delete()
                    await message.reply_photo(
                        BufferedInputFile(image_data, filename="generated.png"),
                        caption=f"🎨 <b>Сгенерировано по запросу:</b>\n<i>{prompt[:200]}</i>",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await processing_msg.edit_text("❌ Не удалось сгенерировать изображение. Попробуйте другой запрос.")
                    
            except asyncio.TimeoutError:
                await processing_msg.edit_text("⏱ Генерация заняла слишком много времени. Попробуйте позже.")
            except Exception as e:
                logger.error(f"Image generation error: {e}")
                await processing_msg.edit_text("❌ Ошибка при генерации изображения.")
        
        @self.dp.message(lambda msg: msg.text and "Сгенерировать картинку" in msg.text)
        async def btn_generate_image(message: Message):
            if await self.check_banned(message):
                return
            await message.reply(
                "🎨 <b>Генерация изображений</b>\n\n"
                "Отправьте: <code>/image ваше описание</code>\n\n"
                "Например: <code>/image закат на море, фотореалистично</code>",
                parse_mode=ParseMode.HTML
            )
        
        # ===== NEWS =====
        @self.dp.message(lambda msg: msg.text and "Новости" in msg.text)
        async def btn_news(message: Message):
            if await self.check_banned(message):
                return
            
            await self.bot.send_chat_action(message.chat.id, "typing")
            
            try:
                # Get news for Kyrgyzstan by default
                news = self.news_agg.get_news_by_category("kyrgyzstan", limit=5)
                
                if not news:
                    await message.reply("📰 Новости временно недоступны. Попробуйте позже.")
                    return
                
                text = "📰 <b>Последние новости Кыргызстана</b>\n\n"
                for i, item in enumerate(news, 1):
                    title = item.get('title', 'Без заголовка')
                    source = item.get('source', 'Неизвестный источник')
                    text += f"{i}. <b>{title}</b>\n   📌 {source}\n\n"
                
                text += "💡 Используйте <code>/digest</code> для AI анализа новостей"
                await message.reply(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                
            except Exception as e:
                logger.error(f"News error: {e}")
                await message.reply("❌ Ошибка при получении новостей.")
        
        @self.dp.message(Command("digest"))
        async def get_digest(message: Message):
            if await self.check_banned(message):
                return
            
            await self.bot.send_chat_action(message.chat.id, "typing")
            
            try:
                digest = self.news_agg.generate_digest("kyrgyzstan")
                
                if digest:
                    # Split if too long
                    if len(digest) > 4000:
                        parts = [digest[i:i+4000] for i in range(0, len(digest), 4000)]
                        for i, part in enumerate(parts):
                            header = f"📰 <b>AI Дайджест (часть {i+1}/{len(parts)})</b>\n\n" if len(parts) > 1 else "📰 <b>AI Дайджест</b>\n\n"
                            await message.reply(header + part, parse_mode=ParseMode.HTML)
                    else:
                        await message.reply(f"📰 <b>AI Дайджест</b>\n\n{digest}", parse_mode=ParseMode.HTML)
                else:
                    await message.reply("❌ Не удалось сгенерировать дайджест.")
                    
            except Exception as e:
                logger.error(f"Digest error: {e}")
                await message.reply("❌ Ошибка при генерации дайджеста.")
        
        @self.dp.message(lambda msg: msg.text and "AI Дайджест" in msg.text)
        async def btn_digest(message: Message):
            """Handle AI Digest button."""
            if await self.check_banned(message):
                return
            
            await self.bot.send_chat_action(message.chat.id, "typing")
            
            try:
                digest = self.news_agg.generate_digest("kyrgyzstan")
                
                if digest:
                    # Split if too long
                    if len(digest) > 4000:
                        parts = [digest[i:i+4000] for i in range(0, len(digest), 4000)]
                        for i, part in enumerate(parts):
                            header = f"📰 <b>AI Дайджест (часть {i+1}/{len(parts)})</b>\n\n" if len(parts) > 1 else "📰 <b>AI Дайджест</b>\n\n"
                            await message.reply(header + part, parse_mode=ParseMode.HTML)
                    else:
                        await message.reply(f"📰 <b>AI Дайджест</b>\n\n{digest}", parse_mode=ParseMode.HTML)
                else:
                    await message.reply("❌ Не удалось сгенерировать дайджест.")
                    
            except Exception as e:
                logger.error(f"Digest button error: {e}")
                await message.reply("❌ Ошибка при генерации дайджеста.")
        
        # ===== CONTACTS =====
        @self.dp.message(lambda msg: msg.text and "Контакты" in msg.text)
        async def btn_contacts(message: Message):
            """Handle contacts button."""
            if await self.check_banned(message):
                return
            
            user_id = message.from_user.id
            contacts = self.db.get_contacts(user_id)
            
            # Create inline keyboard for contact actions
            inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить контакт", callback_data="contact_add")],
                [InlineKeyboardButton(text="🔍 Поиск", callback_data="contact_search")],
                [InlineKeyboardButton(text="📋 Все контакты", callback_data="contact_list")]
            ])
            
            if contacts:
                text = f"📇 <b>Ваши контакты</b> ({len(contacts)}):\n\n"
                for c in contacts[:5]:
                    name = c.get('name', 'Без имени')
                    phone = c.get('phone', 'Нет телефона')
                    text += f"• <b>{name}</b> - {phone}\n"
                if len(contacts) > 5:
                    text += f"\n... и ещё {len(contacts) - 5} контактов"
            else:
                text = "📇 <b>Контакты</b>\n\nУ вас пока нет сохранённых контактов.\n\nНажмите «Добавить контакт» чтобы создать первый контакт."
            
            await message.reply(text, parse_mode=ParseMode.HTML, reply_markup=inline_kb)
        
        @self.dp.callback_query(lambda c: c.data and c.data.startswith("contact_"))
        async def callback_contacts(callback_query: types.CallbackQuery):
            """Handle contact callbacks."""
            action = callback_query.data.replace("contact_", "")
            user_id = callback_query.from_user.id
            
            if action == "add":
                self.user_states[user_id] = "awaiting_contact_name"
                await callback_query.message.edit_text(
                    "➕ <b>Добавление контакта</b>\n\n"
                    "Введите имя контакта:",
                    parse_mode=ParseMode.HTML
                )
            
            elif action == "search":
                self.user_states[user_id] = "awaiting_contact_search"
                await callback_query.message.edit_text(
                    "🔍 <b>Поиск контакта</b>\n\n"
                    "Введите имя или телефон для поиска:",
                    parse_mode=ParseMode.HTML
                )
            
            elif action == "list":
                contacts = self.db.get_contacts(user_id)
                if contacts:
                    text = f"📋 <b>Все контакты</b> ({len(contacts)}):\n\n"
                    for c in contacts:
                        name = c.get('name', 'Без имени')
                        phone = c.get('phone', 'Нет телефона')
                        text += f"• <b>{name}</b>\n  📞 {phone}\n\n"
                else:
                    text = "📋 У вас нет сохранённых контактов."
                
                await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML)
            
            await callback_query.answer()
        
        # ===== HELP =====
        @self.dp.message(lambda msg: msg.text and "Помощь" in msg.text)
        async def btn_help(message: Message):
            """Handle help button."""
            await cmd_help(message)
        
        # ===== CRYPTO =====
        @self.dp.message(lambda msg: msg.text and "Криптовалюта" in msg.text)
        async def btn_crypto(message: Message):
            if await self.check_banned(message):
                return
            
            try:
                # Get top crypto prices
                btc = crypto.get_price("bitcoin")
                eth = crypto.get_price("ethereum")
                
                text = "💰 <b>Криптовалюты</b>\n\n"
                
                if btc:
                    text += f"<b>Bitcoin (BTC)</b>\n💵 ${btc.get('usd', 'N/A')}\n📊 24ч: {btc.get('usd_24h_change', 0):.2f}%\n\n"
                
                if eth:
                    text += f"<b>Ethereum (ETH)</b>\n💵 ${eth.get('usd', 'N/A')}\n📊 24ч: {eth.get('usd_24h_change', 0):.2f}%\n\n"
                
                text += "💡 Используйте кнопку <b>📈 Мой портфель</b> для отслеживания ваших криптовалют"
                
                await message.reply(text, parse_mode=ParseMode.HTML)
                
            except Exception as e:
                logger.error(f"Crypto error: {e}")
                await message.reply("❌ Ошибка при получении данных о криптовалютах.")
        
        @self.dp.message(lambda msg: msg.text and "Мой портфель" in msg.text)
        async def btn_portfolio(message: Message):
            if await self.check_banned(message):
                return
            
            user_id = message.from_user.id
            portfolio = crypto.get_portfolio(user_id)
            
            if not portfolio:
                await message.reply(
                    "📈 <b>Ваш портфель пуст</b>\n\n"
                    "Добавьте криптовалюты через кнопку 💰 Криптовалюта",
                    parse_mode=ParseMode.HTML
                )
                return
            
            try:
                text = "📈 <b>Мой крипто-портфель</b>\n\n"
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
                        
                        text += f"{emoji} <b>{coin_id.upper()}</b>: {amount} шт. = ${value:.2f}\n"
                
                text += f"\n💰 <b>Общая стоимость: ${total_value:.2f}</b>"
                await message.reply(text, parse_mode=ParseMode.HTML)
                
            except Exception as e:
                logger.error(f"Portfolio error: {e}")
                await message.reply("❌ Ошибка при получении портфеля.")
        
        # ===== ADMIN PANEL =====
        @self.dp.message(lambda msg: msg.text and "Админ" in msg.text)
        async def btn_admin(message: Message):
            if not self.is_admin(message.from_user.id):
                await message.reply("⛔ У вас нет доступа к админ-панели.")
                return
            
            stats = self.db.get_stats()
            
            text = (
                "👤 <b>Админ-панель</b>\n\n"
                f"📊 Статистика:\n"
                f"• Пользователей: {stats.get('total_users', 0)}\n"
                f"• Сообщений: {stats.get('total_messages', 0)}\n\n"
                f"<b>Команды:</b>\n"
                f"/broadcast [текст] - Рассылка\n"
                f"/user_info [id] - Инфо о пользователе\n"
                f"/ban [id] [причина] - Забанить\n"
                f"/unban [id] - Разбанить"
            )
            await message.reply(text, parse_mode=ParseMode.HTML)
        
        @self.dp.message(Command("broadcast"))
        async def broadcast_message(message: Message):
            if not self.is_admin(message.from_user.id):
                return
            
            text = message.text.replace("/broadcast", "").strip()
            if not text:
                await message.reply("Использование: /broadcast текст сообщения")
                return
            
            users = self.db.get_all_users()
            sent = 0
            failed = 0
            
            status_msg = await message.reply(f"📤 Начинаю рассылку для {len(users)} пользователей...")
            
            for user in users:
                try:
                    await self.bot.send_message(user['id'], f"📢 <b>Сообщение от администратора</b>\n\n{text}", parse_mode=ParseMode.HTML)
                    sent += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"Broadcast failed for {user['id']}: {e}")
            
            await status_msg.edit_text(f"✅ Рассылка завершена\n\n📤 Отправлено: {sent}\n❌ Не доставлено: {failed}")
        
        # ===== TEXT HANDLER (for states and general messages) =====
        @self.dp.message()
        async def handle_text(message: Message):
            if await self.check_banned(message):
                return
            
            user_id = message.from_user.id
            text = message.text.strip()
            
            # Check user state
            if user_id in self.user_states:
                state = self.user_states[user_id]
                del self.user_states[user_id]
                
                if state == "awaiting_cny_amount":
                    result = convert_cny_to_kgs(text)
                    await message.reply(format_conversion_result(result), parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard(user_id))
                    return
                
                elif state == "awaiting_kgs_amount":
                    result = convert_kgs_to_cny(text)
                    await message.reply(format_conversion_result(result), parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard(user_id))
                    return
                
                # ===== CONTACT STATES =====
                elif state == "awaiting_contact_name":
                    # Store temp contact name and ask for phone
                    self.user_states[user_id] = {"state": "awaiting_contact_phone", "name": text}
                    await message.reply(
                        f"➕ <b>Добавление контакта</b>\n\n"
                        f"Имя: <b>{text}</b>\n\n"
                        f"Теперь введите номер телефона:",
                        parse_mode=ParseMode.HTML
                    )
                    return
                
                elif isinstance(state, dict) and state.get("state") == "awaiting_contact_phone":
                    # Save contact
                    name = state.get("name", "Без имени")
                    phone = text
                    
                    try:
                        self.db.add_contact(name, phone, user_id)
                        await message.reply(
                            f"✅ <b>Контакт сохранён!</b>\n\n"
                            f"📇 <b>{name}</b>\n"
                            f"📞 {phone}",
                            parse_mode=ParseMode.HTML,
                            reply_markup=get_main_keyboard(user_id)
                        )
                    except Exception as e:
                        logger.error(f"Error saving contact: {e}")
                        await message.reply("❌ Ошибка при сохранении контакта.", reply_markup=get_main_keyboard(user_id))
                    return
                
                elif state == "awaiting_contact_search":
                    # Search contacts (filter by user's contacts)
                    all_contacts = self.db.get_contacts(user_id)
                    query = text.lower()
                    contacts = [c for c in all_contacts if query in c.get('name', '').lower() or query in c.get('phone', '').lower()]
                    
                    if contacts:
                        result_text = f"🔍 <b>Результаты поиска</b> '{text}':\n\n"
                        for c in contacts:
                            name = c.get('name', 'Без имени')
                            phone = c.get('phone', 'Нет телефона')
                            note = c.get('note', '')
                            result_text += f"📇 <b>{name}</b>\n📞 {phone}"
                            if note:
                                result_text += f"\n📝 {note}"
                            result_text += "\n\n"
                    else:
                        result_text = f"🔍 По запросу '{text}' ничего не найдено."
                    
                    await message.reply(result_text, parse_mode=ParseMode.HTML, reply_markup=get_main_keyboard(user_id))
                    return
            
            # Check if it's a direct question (AI chat without /gpt4)
            if len(text) > 10 and text.endswith("?"):
                # User asked a question - offer AI help
                await message.reply(
                    f"❓ <b>Я не уверен, что вы имели в виду...</b>\n\n"
                    f"Если вы хотите поговорить с AI, используйте:\n"
                    f"<code>/gpt4 {text}</code>\n\n"
                    f"Или выберите действие в меню 👇",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_main_keyboard(user_id)
                )
                return
            
            # Default response
            await message.reply(
                "❓ Не понял команду.\n\n"
                "Выберите действие в меню или используйте /help",
                reply_markup=get_main_keyboard(user_id)
            )
    
    async def run(self):
        """Start Telegram bot polling."""
        if not self.enabled:
            logger.warning("Telegram bot is disabled (no token)")
            return
        
        logger.info("Full Telegram bot started!")
        
        # Start news scheduler in background
        scheduler_task = asyncio.create_task(self._run_scheduler())
        
        try:
            await self.dp.start_polling(self.bot)
        finally:
            scheduler_task.cancel()
    
    async def _run_scheduler(self):
        """Run news scheduler in background."""
        try:
            scheduler = NewsScheduler(self.db)
            while True:
                try:
                    run_scheduler_once(scheduler, self.news_agg, self.bot)
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(3600)  # Check every hour
        except asyncio.CancelledError:
            logger.info("Scheduler stopped")


async def run_full_telegram_bot():
    """Entry point for running full Telegram bot."""
    bot = FullTelegramBot()
    if bot.enabled:
        await bot.run()
    else:
        logger.warning("Full Telegram bot not started - token missing")
