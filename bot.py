import logging
import os
import json
import tempfile
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, BufferedInputFile, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import asyncio
import requests
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET
from database import Database
from news_scheduler import NewsScheduler, run_scheduler_once
from news_aggregator import NewsAggregator
from image_generator import ImageGenerator, DeepSeekChat
from crypto_tracker import crypto

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

# Function to clean text for TTS
def clean_text_for_tts(text):
    # Remove emojis and special characters, keep only letters, numbers, and spaces
    text = re.sub(r'[^\w\s]', '', text)
    return text

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load config (safe)
config = {}
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    logging.warning('config.json not found, using defaults and environment variables.')
except json.JSONDecodeError as e:
    logging.error(f'Invalid config.json: {e}. Using defaults and environment variables.')

# Initialize bot and dispatcher
API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN", "7968782605:AAEyELGMhUCMwzHH7FglYs9oL4Hi0Ew7CkQ")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or config.get("openrouter_api_key", "")
key_source = "env" if os.environ.get("OPENROUTER_API_KEY") else "config"
logging.info(f'OPENROUTER_API_KEY source: {key_source}, length: {len(OPENROUTER_API_KEY)}')
logging.info(f'OPENROUTER_API_KEY value: {OPENROUTER_API_KEY[:25]}...')
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", config.get("weather_api_key", "YOUR_OPENWEATHERMAP_API_KEY"))

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Webhook configuration (for production)
WEBHOOK_HOST = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")  # Railway provides this automatically
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else ""

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Initialize database
db = Database()

# Initialize AI services
image_gen = ImageGenerator()
deepseek_chat = DeepSeekChat()

# Dictionary for temporary states (password input, etc.)
user_states = {}

# Admin configuration
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # Главный админ (из env)

def is_admin(user_id: int) -> bool:
    """Check if user is admin (main or from database)"""
    if user_id == ADMIN_ID:
        return True
    return db.is_admin(user_id)

def is_banned(user_id: int) -> bool:
    """Check if user is banned"""
    return db.is_banned(user_id) is not None

async def check_banned(message: types.Message) -> bool:
    """Check and notify if user is banned"""
    ban_info = db.is_banned(message.from_user.id)
    if ban_info:
        await message.reply(
            f"⛔ <b>Вы заблокированы</b>\n\n"
            f"Причина: {ban_info.get('reason', 'Не указана')}\n"
            f"Дата блокировки: {ban_info.get('banned_at', 'Неизвестно')[:10]}",
            parse_mode='HTML'
        )
        return True
    return False

# Warn if OpenRouter key missing
if not OPENROUTER_API_KEY:
    logging.warning('OPENROUTER_API_KEY is not set. OpenRouter requests will fail.')

# Main reply keyboard shown under the input field
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Погода Бишкек'), KeyboardButton(text='Погода Москва')],
        [KeyboardButton(text='Погода Иссык-Куль'), KeyboardButton(text='Погода Боконбаево'), KeyboardButton(text='Погода Тон')],
        [KeyboardButton(text='Курс валют'), KeyboardButton(text='Новости'), KeyboardButton(text='Контакты')],
        [KeyboardButton(text='🎨 Сгенерировать картинку'), KeyboardButton(text='📰 AI Дайджест')],
        [KeyboardButton(text='💰 Криптовалюты'), KeyboardButton(text='📈 Мой портфель')],
        [KeyboardButton(text='🇨🇳 Юань → Сом'), KeyboardButton(text='🇰🇬 Сом → Юань')],
        [KeyboardButton(text='Переключить голос'), KeyboardButton(text='Голосовой ответ'), KeyboardButton(text='👤 Админ')]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

async def show_all_contacts(message: types.Message):
    """Show all contacts from database"""
    user_id = message.from_user.id
    contacts_list = db.get_all_contacts()
    
    if not contacts_list:
        # Show keyboard with Add Contact button
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить контакт", callback_data="contact:add")]
        ])
        await message.reply('Список контактов пуст. Добавьте первый контакт!', reply_markup=kb)
        return
    
    rows = []
    for contact in contacts_list:
        rows.append([InlineKeyboardButton(
            text=contact['name'], 
            callback_data=f"contact:{contact['id']}"
        )])
    
    rows.append([InlineKeyboardButton(text="➕ Добавить контакт", callback_data="contact:add")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.reply('Выберите контакт:', reply_markup=kb)


async def contact_callback_handler(callback: types.CallbackQuery):
    data = callback.data or ''
    user_id = callback.from_user.id
    await callback.answer()
    
    if not is_authenticated(user_id):
        await callback.message.reply('Доступ закрыт. Пожалуйста, авторизуйтесь через /start.')
        return
    
    if not data.startswith('contact:'):
        return
    
    action = data.split(':', 1)[1]
    
    if action == 'add':
        # Start adding contact process
        user_states[user_id] = {'awaiting_contact_name': True}
        await callback.message.reply('Введите имя контакта:')
        return
    
    if action == 'back':
        await show_all_contacts(callback.message)
        return
    
    # Show contact details
    try:
        contact_id = int(action)
        contact = db.get_contact_by_id(contact_id)
        if contact:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Вернуться', callback_data='contact:back')]
            ])
            await callback.message.reply(
                f"👤 {contact['name']}\n📞 {contact['phone']}", 
                reply_markup=kb
            )
        else:
            await callback.message.reply('Контакт не найден.')
    except ValueError:
        await callback.message.reply('Ошибка: неверный ID контакта.')

# Password protection
AUTH_PASSWORD = "1916"
authenticated_users = set()

def is_authenticated(user_id: int) -> bool:
    return user_id in authenticated_users

async def ensure_auth(message: types.Message) -> bool:
    user_id = message.from_user.id
    
    # Check if banned
    if await check_banned(message):
        return False
    
    if is_authenticated(user_id):
        return True
    await message.reply('Доступ закрыт. Отправьте /start и введите пароль.')
    return False

# Function to query OpenRouter API (sync) with fallback models
def query_deepseek_sync(messages):
    if not OPENROUTER_API_KEY:
        return "OPENROUTER_API_KEY не установлен. Установите переменную окружения OPENROUTER_API_KEY."
    
    # List of models to try (with fallback)
    models_to_try = [
        config.get("default_model", "openrouter/free"),
        "deepseek/deepseek-r1-0528:free",
        "arcee-ai/trinity-large-preview:free",
        "tngtech/deepseek-tng-r1t2-chimera:free",
        "stepfun/step-3.5-flash:free",
        "google/gemini-2.5-flash-lite"
    ]
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    last_error = None
    
    for model in models_to_try:
        try:
            logging.info(f"[OpenRouter] Попытка использовать модель: {model}")
            
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": 1000
            }
            
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=60)
            
            # Handle rate limiting
            if response.status_code == 429:
                logging.warning(f"[OpenRouter] Модель {model} достигла лимита (429), пробуем следующую...")
                continue
            
            # Handle auth error
            if response.status_code == 401:
                logging.error("Ошибка 401: Неверный токен авторизации для OpenRouter API.")
                return "❌ Ошибка 401: Неверный токен авторизации. Проверьте OPENROUTER_API_KEY."
            
            # Handle bad request
            if response.status_code == 400:
                logging.warning(f"[OpenRouter] Модель {model} вернула 400, пробуем следующую...")
                continue
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the message content from the response
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                logging.info(f"[OpenRouter] Успешно использована модель: {model}")
                return content
            
            logging.warning(f"[OpenRouter] Модель {model} вернула пустой ответ, пробуем следующую...")
            
        except requests.exceptions.Timeout:
            logging.warning(f"[OpenRouter] Таймаут модели {model}, пробуем следующую...")
            last_error = "Таймаут"
        except requests.exceptions.RequestException as e:
            logging.warning(f"[OpenRouter] Ошибка модели {model}: {e}")
            last_error = str(e)
            continue
    
    # All models failed
    error_msg = f"❌ Все модели недоступны. Последняя ошибка: {last_error}\n\n"
    error_msg += "💡 Причины:\n"
    error_msg += "• Достигнут дневной лимит free моделей (200 запросов/день)\n"
    error_msg += "• Высокая нагрузка на серверы\n"
    error_msg += "• Модели временно недоступны\n\n"
    error_msg += "⏰ Попробуйте позже или завтра."
    
    logging.error(f"[OpenRouter] Все модели исчерпаны: {last_error}")
    return error_msg

# Async wrapper for query_deepseek
async def query_deepseek(messages):
    return await asyncio.to_thread(query_deepseek_sync, messages)

# Sync function to generate voice
def generate_voice_sync(text, lang='ru'):
    if not TTS_AVAILABLE:
        return None
    text = clean_text_for_tts(text)
    try:
        tts = gTTS(text, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            tts.save(temp_file.name)
            logging.info("Голос сгенерирован успешно")
            return temp_file.name
    except Exception as e:
        logging.error(f"Ошибка при генерации голоса: {e}")
        # Clean up temp file if it was created
        try:
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        except Exception:
            pass
        return None

# Edge-TTS voice generation
async def generate_voice_edge(text, voice="ru-RU-SvetlanaNeural"):
    """
    Generate voice using Edge-TTS (Microsoft Edge voices).
    Russian voices: ru-RU-SvetlanaNeural (female), ru-RU-DmitryNeural (male)
    """
    if not EDGE_TTS_AVAILABLE:
        return None
    try:
        # Limit text length
        text = text[:3000]
        communicate = edge_tts.Communicate(text, voice)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            await communicate.save(temp_file.name)
            logging.info(f"Edge-TTS voice generated successfully with voice: {voice}")
            return temp_file.name
    except Exception as e:
        logging.error(f"Ошибка Edge-TTS: {e}")
        return None

# ========== SPEECH RECOGNITION (Whisper) ==========

async def transcribe_voice(voice_file_path: str) -> str:
    """Transcribe voice message using OpenAI Whisper via OpenRouter"""
    try:
        url = "https://openrouter.ai/api/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}"
        }
        
        with open(voice_file_path, 'rb') as audio_file:
            files = {'file': audio_file}
            data = {'model': 'openai/whisper-1'}
            
            response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('text', '')
            else:
                logging.error(f"Whisper error: {response.status_code} - {response.text}")
                return ""
    except Exception as e:
        logging.error(f"Error transcribing voice: {e}")
        return ""

# Async wrapper for generate_voice (tries Edge-TTS first, falls back to gTTS)
async def generate_voice(text, lang='ru'):
    # Try Edge-TTS first (better quality)
    if EDGE_TTS_AVAILABLE:
        voice_file = await generate_voice_edge(text)
        if voice_file:
            return voice_file
    
    # Fallback to gTTS if Edge-TTS failed or unavailable
    if TTS_AVAILABLE:
        return await asyncio.to_thread(generate_voice_sync, text, lang)
    
    return None

# Function to get weather
def get_weather(city):
    # Geocode the city
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ru"
    try:
        geo_response = requests.get(geo_url)
        if geo_response.status_code != 200:
            return "Не удалось найти город."
        geo_data = geo_response.json()
        if 'results' not in geo_data or len(geo_data['results']) == 0:
            return "Город не найден."
        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']

        # Get weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
        weather_response = requests.get(weather_url)
        if weather_response.status_code == 200:
            weather_data = weather_response.json()
            temp = weather_data['current_weather']['temperature']
            weathercode = weather_data['current_weather']['weathercode']
            # Decode weathercode to description with emojis
            descriptions = {
                0: "☀️ ясно", 1: "🌤️ преимущественно ясно", 2: "⛅ переменная облачность", 3: "☁️ пасмурно",
                45: "🌫️ туман", 48: "🌧️ изморось", 51: "🌦️ мелкий дождь", 53: "🌧️ дождь", 55: "🌧️ сильный дождь",
                56: "🧊 ледяной дождь", 57: "🧊 сильный ледяной дождь", 61: "🌦️ небольшой дождь", 63: "🌧️ дождь", 65: "🌧️ сильный дождь",
                66: "🧊 ледяной дождь", 67: "🧊 сильный ледяной дождь", 71: "❄️ небольшой снег", 73: "❄️ снег", 75: "❄️ сильный снег",
                77: "🌨️ снежные зерна", 80: "🌦️ небольшой дождь", 81: "🌧️ дождь", 82: "🌧️ сильный дождь",
                85: "❄️ небольшой снег", 86: "❄️ сильный снег", 95: "⛈️ гроза", 96: "⛈️ гроза с градом", 99: "⛈️ сильная гроза с градом"
            }
            description = descriptions.get(weathercode, "❓ неизвестно")
            return f"🌤️ Погода в {city}: {temp}°C, {description}"
        else:
            return "Не удалось получить данные о погоде."
    except Exception as e:
        logging.error(f"Ошибка при получении погоды: {e}")
        return "Ошибка при подключении к API погоды."

# Function to get currency rates
def get_currency():
    url = config.get("currency_api_url", "https://api.exchangerate-api.com/v4/latest/USD")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            usd_to_kgs = data['rates']['KGS']
            usd_to_rub = data['rates']['RUB']
            return f"💰 Курс USD: KGS {usd_to_kgs:.2f}, RUB {usd_to_rub:.2f}"
        else:
            return "Не удалось получить данные о валюте."
    except Exception as e:
        logging.error(f"Ошибка при получении валюты: {e}")
        return "Ошибка при подключении к API валюты."

# Function to get CNY (Chinese Yuan) rate
def get_cny_rate():
    """Get CNY to KGS exchange rate"""
    try:
        # Using exchangerate-api for CNY
        url = "https://api.exchangerate-api.com/v4/latest/CNY"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            cny_to_kgs = data['rates'].get('KGS')
            if cny_to_kgs:
                return cny_to_kgs
        # Fallback: try USD-based calculation
        url_usd = "https://api.exchangerate-api.com/v4/latest/USD"
        response_usd = requests.get(url_usd, timeout=10)
        if response_usd.status_code == 200:
            data_usd = response_usd.json()
            usd_to_kgs = data_usd['rates'].get('KGS')
            usd_to_cny = data_usd['rates'].get('CNY')
            if usd_to_kgs and usd_to_cny:
                return usd_to_kgs / usd_to_cny
        return None
    except Exception as e:
        logging.error(f'Ошибка при получении курса юаня: {e}')
        return None

# Function to format number with spaces
def format_number(num):
    """Format number with spaces as thousand separators"""
    return f"{num:,.2f}".replace(",", " ")

@dp.message(lambda message: message.text == '🇨🇳 Юань → Сом')
async def cny_to_kgs_handler(message: types.Message):
    """Handle CNY to KGS conversion"""
    user_id = message.from_user.id
    if await check_banned(message):
        return
    
    # Set user state to wait for amount
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]['awaiting_cny_amount'] = 'cny_to_kgs'
    
    # Get current rate for display
    rate = get_cny_rate()
    if rate:
        await message.reply(
            f"🇨🇳 <b>Конвертер: Юань → Сом</b>\n\n"
            f"📊 Текущий курс: <b>1 CNY = {rate:.2f} KGS</b>\n\n"
            f"💬 Введите сумму в юанях (CNY):",
            parse_mode='HTML'
        )
    else:
        await message.reply(
            "🇨🇳 <b>Конвертер: Юань → Сом</b>\n\n"
            "💬 Введите сумму в юанях (CNY):",
            parse_mode='HTML'
        )

@dp.message(lambda message: message.text == '🇰🇬 Сом → Юань')
async def kgs_to_cny_handler(message: types.Message):
    """Handle KGS to CNY conversion"""
    user_id = message.from_user.id
    if await check_banned(message):
        return
    
    # Set user state to wait for amount
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]['awaiting_cny_amount'] = 'kgs_to_cny'
    
    # Get current rate for display
    rate = get_cny_rate()
    if rate:
        await message.reply(
            f"🇰🇬 <b>Конвертер: Сом → Юань</b>\n\n"
            f"📊 Текущий курс: <b>1 CNY = {rate:.2f} KGS</b>\n\n"
            f"💬 Введите сумму в сомах (KGS):",
            parse_mode='HTML'
        )
    else:
        await message.reply(
            "🇰🇬 <b>Конвертер: Сом → Юань</b>\n\n"
            "💬 Введите сумму в сомах (KGS):",
            parse_mode='HTML'
        )

async def process_cny_conversion(message: types.Message, conversion_type: str):
    """Process CNY conversion after user inputs amount"""
    try:
        amount = float(message.text.replace(',', '.').strip())
        if amount <= 0:
            await message.reply("❌ Сумма должна быть больше 0!")
            return
        
        rate = get_cny_rate()
        if not rate:
            await message.reply("❌ Не удалось получить курс валюты. Попробуйте позже.")
            return
        
        if conversion_type == 'cny_to_kgs':
            result = amount * rate
            await message.reply(
                f"🇨🇳 <b>Конвертация: Юань → Сом</b>\n\n"
                f"💵 Сумма: <b>{amount:,.2f} CNY</b>\n"
                f"📊 Курс: 1 CNY = {rate:.2f} KGS\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💰 Результат: <b>{result:,.2f} KGS</b>",
                parse_mode='HTML'
            )
        else:  # kgs_to_cny
            result = amount / rate
            await message.reply(
                f"🇰🇬 <b>Конвертация: Сом → Юань</b>\n\n"
                f"💵 Сумма: <b>{amount:,.2f} KGS</b>\n"
                f"📊 Курс: 1 CNY = {rate:.2f} KGS\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💰 Результат: <b>{result:,.2f} CNY</b>",
                parse_mode='HTML'
            )
    except ValueError:
        await message.reply("❌ Пожалуйста, введите число (например: 100 или 150.50)")
    except Exception as e:
        logging.error(f'Ошибка конвертации: {e}')
        await message.reply("❌ Ошибка при конвертации. Попробуйте позже.")

# Function to get news from Kyrgyzstan via RSS
def get_news_kyrgyzstan():
    rss_url = config.get("rss_url", "https://kaktus.media/?rss")
    try:
        response = requests.get(rss_url)
        if response.status_code != 200:
            return "Не удалось получить RSS фид."
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        if not items:
            return "Новости не найдены."
        now = datetime.now(timezone.utc)
        three_days_ago = now - timedelta(days=3)
        recent_news = []
        for item in items:
            pubdate_elem = item.find('pubDate')
            if pubdate_elem is not None:
                try:
                    # Parse RSS date, typically in format like "Wed, 02 Oct 2019 07:00:00 +0000"
                    pubdate_str = pubdate_elem.text
                    pubdate = datetime.strptime(pubdate_str, "%a, %d %b %Y %H:%M:%S %z")
                    if pubdate > three_days_ago:
                        title_elem = item.find('title')
                        title = title_elem.text if title_elem is not None else 'Без заголовка'
                        link_elem = item.find('link')
                        url = link_elem.text if link_elem is not None else ''
                        recent_news.append(f"📰 {title}\n🔗 {url}")
                except ValueError:
                    continue  # Skip if date parsing fails
            if len(recent_news) >= 5:
                break
        if not recent_news:
            return "❌ Нет новостей за последние 3 дня."
        return "📰 Новости Киргизстана за последние 3 дня:\n\n" + "\n\n".join(recent_news)
    except Exception as e:
        logging.error(f"Ошибка при получении новостей: {e}")
        return "Ошибка при подключении к RSS."

# Command handler for /start
async def send_welcome(message: types.Message):
    logging.info(f"Получена команда /start от пользователя {message.from_user.id}")
    user_id = message.from_user.id
    
    # Check if user is banned
    if await check_banned(message):
        return
    
    # Save user to database
    db.add_or_update_user(
        telegram_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Initialize user state if needed
    if user_id not in user_states:
        user_states[user_id] = {}

    # If already authenticated, show menu
    if is_authenticated(user_id):
        menu = (
            "🌟 Привет! Я ИИ-бот. 🤖\n"
            "📋 Доступные команды:\n\n"
            "<b>🌤 Погода:</b>\n"
            "☀️ /weather_bishkek - Погода в Бишкеке\n"
            "❄️ /weather_moscow - Погода в Москве\n"
            "🏞️ /weather_issykkul - Погода в Иссык-Куле\n"
            "🏔️ /weather_bokonbaevo - Погода в Боконбаево\n"
            "🌄 /weather_ton - Погода в Тоне\n\n"
            "<b>💰 Финансы:</b>\n"
            "💰 /currency - Курс валют\n"
            "🇨🇳 Юань → Сом - Конвертер CNY в KGS\n"
            "🇰🇬 Сом → Юань - Конвертер KGS в CNY\n\n"
            "<b>📰 Новостной дайджест с AI:</b>\n"
            "📋 /interests - Мои интересы\n"
            "📰 /digest - Получить дайджест сейчас\n"
            "📅 /schedule - Настроить расписание\n\n"
            "<b>🎨 AI Генерация:</b>\n"
            "🎨 /image &lt;описание&gt; - Сгенерировать картинку (бесплатно)\n"
            "🧠 /gpt4 &lt;вопрос&gt; - DeepSeek R1 (бесплатно)\n\n"
            "<b>🎤 Голос:</b>\n"
            "🎤 /toggle_voice - Переключить голосовой режим\n"
            + ("🎤 /voice [вопрос] - Ответ голосом\n" if TTS_AVAILABLE else "")
            + "\n<b>⚙️ Другое:</b>\n"
            "🗑 /clear_history - Очистить историю чата\n"
            "📊 /stats - Моя статистика\n"
            "📰 /news_kyrgyzstan - Новости Киргизстана (классика)\n\n"
            "💬 Просто напишите свой вопрос, и я отвечу!"
        )
        await message.reply(menu, reply_markup=main_keyboard)
        return

    # Not authenticated: ask for password
    user_states[user_id]['awaiting_password'] = True
    await message.reply('Бот приватный. Введите пароль:')

# Handler for weather in Bishkek
async def weather_bishkek(message: types.Message):
    logging.info(f"Получена команда /weather_bishkek от пользователя {message.from_user.id}")
    if not await ensure_auth(message):
        return
    await message.reply("☀️ Получаю погоду в Бишкеке...")
    response = get_weather("Bishkek")
    await message.reply(response)

# Handler for weather in Moscow
async def weather_moscow(message: types.Message):
    logging.info(f"Получена команда /weather_moscow от пользователя {message.from_user.id}")
    if not await ensure_auth(message):
        return
    await message.reply("❄️ Получаю погоду в Москве...")
    response = get_weather("Moscow")
    await message.reply(response)

# Handler for weather in Issyk-Kul
async def weather_issykkul(message: types.Message):
    logging.info(f"Получена команда /weather_issykkul от пользователя {message.from_user.id}")
    if not await ensure_auth(message):
        return
    await message.reply("🏞️ Получаю погоду в Иссык-Куле...")
    response = get_weather("Issyk-Kul")
    await message.reply(response)

# Handler for weather in Bokonbaevo
async def weather_bokonbaevo(message: types.Message):
    logging.info(f"Получена команда /weather_bokonbaevo от пользователя {message.from_user.id}")
    if not await ensure_auth(message):
        return
    await message.reply("🏔️ Получаю погоду в Боконбаево...")
    response = get_weather("Bokonbaevo")
    await message.reply(response)

# Handler for weather in Ton
async def weather_ton(message: types.Message):
    logging.info(f"Получена команда /weather_ton от пользователя {message.from_user.id}")
    if not await ensure_auth(message):
        return
    await message.reply("🌄 Получаю погоду в Тоне...")
    response = get_weather("Ton")
    await message.reply(response)

# Handler for currency
async def currency(message: types.Message):
    logging.info(f"Получена команда /currency от пользователя {message.from_user.id}")
    if not await ensure_auth(message):
        return
    await message.reply("Получаю курс валют...")
    response = get_currency()
    await message.reply(response)

# Handler for news Kyrgyzstan
async def news_kyrgyzstan(message: types.Message):
    logging.info(f"Получена команда /news_kyrgyzstan от пользователя {message.from_user.id}")
    if not await ensure_auth(message):
        return
    await message.reply("📰 Получаю новости Киргизстана за последние 3 дня...")
    response = get_news_kyrgyzstan()
    await message.reply(response)

# Handler for voice response
async def voice_handler(message: types.Message):
    logging.info(f"Получена команда /voice от пользователя {message.from_user.id}")
    if not await ensure_auth(message):
        return
    if not TTS_AVAILABLE:
        await message.reply("🎤 Функция голосовых ответов недоступна. Установите gtts: pip install gtts")
        return
    user_input = message.text.replace('/voice', '').strip()
    if not user_input:
        await message.reply("🎤 Пожалуйста, укажите вопрос после команды /voice")
        return
    await message.reply("🎤 Обрабатываю ваш вопрос для голосового ответа...")
    response = await query_deepseek([{"role": "user", "content": user_input}])
    voice_fp = await generate_voice(response)
    if voice_fp:
        try:
            await bot.send_voice(message.chat.id, voice=FSInputFile(voice_fp))
            os.unlink(voice_fp)  # Удалить файл после отправки
        except Exception as e:
            logging.error(f"Ошибка при отправке голоса: {e}")
            os.unlink(voice_fp)  # Удалить файл в случае ошибки
            await message.reply("❌ Ошибка при отправке голоса. Отправляю текст.")
            await message.reply(f"🤖 {response}")
    else:
        await message.reply("❌ Ошибка при генерации голоса.")

# Handler for toggle voice mode
async def toggle_voice(message: types.Message):
    user_id = message.from_user.id
    if not await ensure_auth(message):
        return
    current_mode = db.get_voice_mode(user_id)
    new_mode = not current_mode
    db.set_voice_mode(user_id, new_mode)
    status = "включен" if new_mode else "выключен"
    await message.reply(f"🎤 Голосовой режим {status}.")

# Handler for clear history
async def clear_history(message: types.Message):
    user_id = message.from_user.id
    if not await ensure_auth(message):
        return
    db.clear_chat_history(user_id)
    await message.reply("🗑 История чата очищена.")

# Handler for user stats
async def user_stats(message: types.Message):
    user_id = message.from_user.id
    if not await ensure_auth(message):
        return
    stats = db.get_user_stats(user_id)
    await message.reply(
        f"📊 Ваша статистика:\n"
        f"💬 Сообщений: {stats['message_count']}\n"
        f"👤 Контактов добавлено: {stats['contact_count']}"
    )

# Handler for text messages (questions)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    user_input = message.text
    logging.info(f"Получен текст от пользователя {user_id}: {user_input}")

    # If awaiting password, treat message as password attempt
    if user_states.get(user_id, {}).get('awaiting_password'):
        pw = user_input.strip()
        if pw == AUTH_PASSWORD:
            authenticated_users.add(user_id)
            user_states[user_id]['awaiting_password'] = False
            await message.reply('Авторизация успешна.')
            # send menu
            menu = (
                "🌟 Привет! Я ИИ-бот. 🤖\n"
                "📋 Доступные команды:\n"
                "☀️ /weather_bishkek - Погода в Бишкеке\n"
                "❄️ /weather_moscow - Погода в Москве\n"
                "🏞️ /weather_issykkul - Погода в Иссык-Куле\n"
                "🏔️ /weather_bokonbaevo - Погода в Боконбаево\n"
                "🌄 /weather_ton - Погода в Тоне\n"
                "💰 /currency - Курс валют\n"
                "🇨🇳 Юань → Сом - Конвертер CNY в KGS\n"
                "🇰🇬 Сом → Юань - Конвертер KGS в CNY\n"
                "📰 /news_kyrgyzstan - Новости Киргизстана за последние 3 дня\n"
                "🎤 /toggle_voice - Переключить голосовой режим\n"
                "🗑 /clear_history - Очистить историю чата\n"
                "📊 /stats - Моя статистика\n"
                + ("🎤 /voice [вопрос] - Ответ голосом\n" if TTS_AVAILABLE else "")
                + "💬 Просто напишите свой вопрос, и я отвечу!\n"
            )
            await message.reply(menu, reply_markup=main_keyboard)
        else:
            await message.reply('Неверный пароль. Попробуйте ещё раз.')
        return

    # If the user is in contact-search mode, treat this message as the query
    if user_states.get(user_id, {}).get('awaiting_contact_query'):
        query = user_input.strip()
        user_states[user_id]['awaiting_contact_query'] = False
        if not query:
            await message.reply('Пожалуйста, введите имя или номер для поиска контакта.')
            return
        results = db.search_contacts(query)
        if not results:
            await message.reply('Контакты не найдены.')
            return
        lines = [f"{i+1}. {c['name']}: {c['phone']}" for i, c in enumerate(results)]
        await message.reply('Найденные контакты:\n' + '\n'.join(lines))
        return
    
    # ===== MENU BUTTONS - Check first and reset any states =====
    menu_buttons = {
        'Погода Бишкек': 'weather_bishkek',
        'Погода Москва': 'weather_moscow',
        'Погода Иссык-Куль': 'weather_issykkul',
        'Погода Боконбаево': 'weather_bokonbaevo',
        'Погода Тон': 'weather_ton',
        'Курс валют': 'currency',
        'Новости': 'news_kyrgyzstan',
        'Контакты': 'contacts',
        'Переключить голос': 'toggle_voice',
        'Голосовой ответ': 'voice_help',
        '🎨 Сгенерировать картинку': 'image_menu',
        '📰 AI Дайджест': 'digest',
        '💰 Криптовалюты': 'crypto_menu',
        '📈 Мой портфель': 'crypto_portfolio',
        '🇨🇳 Юань → Сом': 'cny_to_kgs',
        '🇰🇬 Сом → Юань': 'kgs_to_cny',
        '👤 Админ': 'admin'
    }
    
    # If user clicked any menu button - reset states and handle the button
    if user_input in menu_buttons:
        # Reset all user states (cancel any pending operations)
        if user_id in user_states:
            had_state = bool(user_states[user_id])
            user_states.pop(user_id, None)
            if had_state:
                await message.reply("❌ Предыдущая операция отменена.")
        
        # Handle the menu button
        if user_input == 'Погода Бишкек':
            await weather_bishkek(message)
        elif user_input == 'Погода Москва':
            await weather_moscow(message)
        elif user_input == 'Погода Иссык-Куль':
            await weather_issykkul(message)
        elif user_input == 'Погода Боконбаево':
            await weather_bokonbaevo(message)
        elif user_input == 'Погода Тон':
            await weather_ton(message)
        elif user_input == 'Курс валют':
            await currency(message)
        elif user_input == 'Новости':
            await news_kyrgyzstan(message)
        elif user_input == 'Переключить голос':
            await toggle_voice(message)
        elif user_input == 'Голосовой ответ':
            await message.reply("Чтобы получить голосовой ответ, используйте: /voice &lt;ваш вопрос&gt;")
        elif user_input == 'Контакты':
            await show_all_contacts(message)
        elif user_input == '🎨 Сгенерировать картинку':
            user_states[user_id] = {'awaiting_image_prompt': True}
            await message.reply("🎨 Опишите, какую картинку хотите сгенерировать:\n\nНапример: «кот в космосе, цифровое искусство»")
        elif user_input == '📰 AI Дайджест':
            await get_digest(message)
        elif user_input == '💰 Криптовалюты':
            await crypto_menu(message)
        elif user_input == '📈 Мой портфель':
            await crypto_portfolio(message)
        elif user_input == '🇨🇳 Юань → Сом':
            await cny_to_kgs_handler(message)
        elif user_input == '🇰🇬 Сом → Юань':
            await kgs_to_cny_handler(message)
        elif user_input == '👤 Админ':
            if is_admin(user_id):
                await admin_panel(message)
            else:
                await message.reply("❌ У вас нет доступа к админ-панели.")
        return
    
    # ===== STATES - Only check if not a menu button =====
    
    # If the user is adding a contact
    if user_states.get(user_id, {}).get('awaiting_contact_name'):
        user_states[user_id]['contact_name'] = user_input.strip()
        user_states[user_id]['awaiting_contact_name'] = False
        user_states[user_id]['awaiting_contact_phone'] = True
        await message.reply('Теперь введите номер телефона:')
        return
    
    if user_states.get(user_id, {}).get('awaiting_contact_phone'):
        phone = user_input.strip()
        name = user_states[user_id].get('contact_name', '')
        if name and phone:
            if db.add_contact(name, phone, user_id):
                await message.reply(f'✅ Контакт добавлен:\n{name}: {phone}')
            else:
                await message.reply('❌ Ошибка при добавлении контакта.')
        else:
            await message.reply('❌ Ошибка: неполные данные.')
        user_states[user_id].pop('contact_name', None)
        user_states[user_id].pop('awaiting_contact_phone', None)
        return
    
    # If the user is converting CNY/KGS
    if user_states.get(user_id, {}).get('awaiting_cny_amount'):
        conversion_type = user_states[user_id].get('awaiting_cny_amount')
        await process_cny_conversion(message, conversion_type)
        user_states[user_id].pop('awaiting_cny_amount', None)
        return
    
    # If the user is generating an image
    if user_states.get(user_id, {}).get('awaiting_image_prompt'):
        prompt = user_input.strip()
        if not prompt:
            await message.reply("❌ Пожалуйста, введите описание для картинки.")
            return
        
        user_states[user_id].pop('awaiting_image_prompt', None)
        
        # Show generating message
        status_msg = await message.reply("🎨 Генерирую изображение... Это может занять 10-30 секунд.")
        
        try:
            # Generate image
            image_path = await asyncio.to_thread(image_gen.generate_image, prompt)
            
            if image_path:
                # Send image
                photo = FSInputFile(image_path)
                await message.reply_photo(photo, caption=f"🎨 «{prompt[:50]}{'...' if len(prompt) > 50 else ''}»")
                await status_msg.delete()
                
                # Clean up temp file
                try:
                    os.remove(image_path)
                except:
                    pass
            else:
                await status_msg.edit_text("❌ Не удалось сгенерировать изображение. Попробуйте другой запрос.")
        except Exception as e:
            logging.error(f"Error generating image: {e}")
            await status_msg.edit_text(f"❌ Ошибка при генерации: {e}")
        return

    # Route friendly keyboard labels to command handlers (fallback)
    if user_input == 'Погода Бишкек':
        await weather_bishkek(message)
        return
    # Save user message to database
    db.add_message(user_id, 'user', user_input)

    # Get chat history from database (last 20 messages)
    history = db.get_chat_history(user_id, limit=20)

    await message.reply("🤖 Обрабатываю ваш вопрос...")
    response = await query_deepseek(history)
    # Limit response length for TTS to avoid issues
    voice_text = response[:2000] if len(response) > 2000 else response
    voice_mode = db.get_voice_mode(user_id)
    
    if voice_mode:
        if TTS_AVAILABLE or EDGE_TTS_AVAILABLE:
            voice_file = await generate_voice(voice_text)
            logging.info(f"Voice file получен: {voice_file is not None}")
            if voice_file:
                logging.info("Отправка голоса")
                try:
                    await bot.send_voice(message.chat.id, voice=FSInputFile(voice_file))
                    logging.info("Голос отправлен успешно")
                    os.unlink(voice_file)  # Удалить файл после отправки
                except Exception as e:
                    logging.error(f"Ошибка при отправке голоса: {e}")
                    os.unlink(voice_file)  # Удалить файл в случае ошибки
                    await message.reply("❌ Ошибка при отправке голоса. Отправляю текст.")
                    await message.reply(f"🤖 {response}")
            else:
                await message.reply("❌ Ошибка при генерации голоса. Отправляю текст.")
                await message.reply(f"🤖 {response}")
        else:
            await message.reply("🎤 Голосовые ответы недоступны. Отправляю текст.")
            await message.reply(f"🤖 {response}")
    else:
        await message.reply(f"🤖 {response}")

    # Save assistant response to database
    db.add_message(user_id, 'assistant', response)

# ========== ADMIN COMMANDS ==========

# Admin states for multi-step operations
admin_states = {}

async def admin_panel(message: types.Message):
    """Admin panel with full statistics and management"""
    if not is_admin(message.from_user.id):
        await message.reply("⛔ Доступ запрещен.")
        return
    
    stats = db.get_admin_stats_extended()
    
    # Create admin keyboard
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin:users")],
        [InlineKeyboardButton(text="🛡️ Управление админами", callback_data="admin:admins")],
        [InlineKeyboardButton(text="🚫 Заблокированные", callback_data="admin:banned")],
        [InlineKeyboardButton(text="📊 Детальная статистика", callback_data="admin:stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin:find_user")],
    ])
    
    await message.reply(
        f"👑 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n\n"
        f"📊 <b>Общая статистика:</b>\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"🟢 Активных сегодня: {stats['active_today']}\n"
        f"📇 Контактов: {stats['total_contacts']}\n"
        f"💬 Сообщений: {stats['total_messages']}\n"
        f"🛡️ Админов: {stats['total_admins']}\n"
        f"🚫 Заблокировано: {stats['total_banned']}\n\n"
        f"<i>Выберите действие:</i>",
        parse_mode='HTML',
        reply_markup=admin_kb
    )

async def broadcast_message(message: types.Message):
    """Broadcast message to all users"""
    if not is_admin(message.from_user.id):
        await message.reply("⛔ Доступ запрещен.")
        return
    
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        await message.reply("Использование: /broadcast &lt;текст&gt;")
        return
    
    # Получаем всех пользователей из БД
    users = db.get_all_users()
    
    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(user['telegram_id'], f"📢 <b>Сообщение от админа:</b>\n\n{text}", parse_mode='HTML')
            sent += 1
        except:
            failed += 1
    
    await message.reply(f"✅ Отправлено: {sent}\n❌ Ошибок: {failed}")

async def user_info(message: types.Message):
    """Get info about specific user"""
    if not is_admin(message.from_user.id):
        await message.reply("⛔ Доступ запрещен.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Использование: /user_info &lt;telegram_id&gt;")
        return
    
    try:
        user_id = int(args[1])
    except ValueError:
        await message.reply("❌ Неверный ID пользователя.")
        return
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        db._execute(cursor, 'SELECT * FROM users WHERE telegram_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            await message.reply("❌ Пользователь не найден.")
            return
        
        stats = db.get_user_stats(user_id)
        
        await message.reply(
            f"👤 <b>Информация о пользователе</b>\n\n"
            f"ID: {user['telegram_id']}\n"
            f"Username: @{user['username'] or 'нет'}\n"
            f"Имя: {user['first_name'] or 'нет'} {user['last_name'] or ''}\n"
            f"Зарегистрирован: {user['created_at']}\n"
            f"Последняя активность: {user['last_active']}\n\n"
            f"📊 Сообщений: {stats['message_count']}\n"
            f"👤 Контактов: {stats['contact_count']}",
            parse_mode='HTML'
        )

async def handle_voice_message(message: types.Message):
    """Handle incoming voice messages"""
    user_id = message.from_user.id
    
    if not await ensure_auth(message):
        return
    
    if not message.voice:
        return
    
    voice = message.voice
    if voice.duration > 60:
        await message.reply("🎤 Голосовое сообщение слишком длинное. Максимум 60 секунд.")
        return
    
    await message.reply("🎤 Распознаю голосовое сообщение...")
    
    try:
        file = await bot.get_file(voice.file_id)
        voice_file_path = tempfile.mktemp(suffix='.ogg')
        await bot.download_file(file.file_path, voice_file_path)
        
        transcribed_text = await transcribe_voice(voice_file_path)
        os.unlink(voice_file_path)
        
        if not transcribed_text:
            await message.reply("❌ Не удалось распознать голосовое сообщение.")
            return
        
        await message.reply(f"📝 <b>Распознанный текст:</b>\n{transcribed_text}", parse_mode='HTML')
        
        db.add_message(user_id, 'user', transcribed_text)
        history = db.get_chat_history(user_id, limit=20)
        
        response = await query_deepseek(history)
        db.add_message(user_id, 'assistant', response)
        
        voice_mode = db.get_voice_mode(user_id)
        if voice_mode and (TTS_AVAILABLE or EDGE_TTS_AVAILABLE):
            voice_text = response[:2000] if len(response) > 2000 else response
            voice_file = await generate_voice(voice_text)
            if voice_file:
                try:
                    await bot.send_voice(message.chat.id, voice=FSInputFile(voice_file))
                    os.unlink(voice_file)
                    return
                except:
                    pass
        
        await message.reply(f"🤖 {response}")
            
    except Exception as e:
        logging.error(f"Error handling voice: {e}")
        await message.reply("❌ Ошибка при обработке голосового сообщения.")

# ========== NEWS DIGEST COMMANDS ==========

async def show_interests(message: types.Message):
    """Show and manage user interests"""
    user_id = message.from_user.id
    if not await ensure_auth(message):
        return
    
    interests = db.get_user_interests(user_id)
    categories = db.get_all_categories()
    
    if not interests:
        interests_text = "❌ Не выбрано"
    else:
        interests_text = ", ".join(f"✅ {c}" for c in interests)
    
    await message.reply(
        f"📰 <b>Ваши интересы:</b>\n{interests_text}\n\n"
        f"Доступные категории:\n" +
        "\n".join([f"/add_{cat} - добавить {cat}" for cat in categories]) + "\n\n"
        f"Удалить: /remove_&lt;категория&gt;\n"
        f"Пример: /add_tech /remove_sports",
        parse_mode='HTML'
    )

async def add_interest_handler(message: types.Message):
    """Add interest from command like /add_tech"""
    user_id = message.from_user.id
    if not await ensure_auth(message):
        return
    
    # Extract category from command
    command = message.text.split()[0].lower().replace('/', '').replace('add_', '')
    
    if db.add_user_interest(user_id, command):
        await message.reply(f"✅ Добавлен интерес: {command}")
    else:
        await message.reply("❌ Не удалось добавить интерес")

async def remove_interest_handler(message: types.Message):
    """Remove interest from command like /remove_tech"""
    user_id = message.from_user.id
    if not await ensure_auth(message):
        return
    
    command = message.text.split()[0].lower().replace('/', '').replace('remove_', '')
    
    if db.remove_user_interest(user_id, command):
        await message.reply(f"❌ Удалён интерес: {command}")
    else:
        await message.reply("❌ Не удалось удалить интерес или категория не найдена")

async def get_digest(message: types.Message):
    """Get news digest immediately"""
    user_id = message.from_user.id
    if not await ensure_auth(message):
        return
    
    scheduler = NewsScheduler(bot, db)
    result = await scheduler.send_digest_now(user_id)
    await scheduler.aggregator.close_session()
    
    if not result.startswith("✅"):
        await message.reply(result)

async def schedule_digest(message: types.Message):
    """Set digest schedule"""
    user_id = message.from_user.id
    if not await ensure_auth(message):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "📅 <b>Настройка расписания</b>\n\n"
            "Использование:\n"
            "/schedule 09:00 - включить на 9:00 утра\n"
            "/schedule off - отключить\n\n"
            "Дайджест будет приходить каждый день в указанное время.",
            parse_mode='HTML'
        )
        return
    
    time_arg = args[1].lower()
    
    if time_arg == 'off':
        db.set_digest_schedule(user_id, False)
        await message.reply("❌ Автоматический дайджест отключен")
    else:
        # Validate time format HH:MM
        import re
        if re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', time_arg):
            db.set_digest_schedule(user_id, True, time_arg)
            await message.reply(f"✅ Дайджест будет приходить каждый день в {time_arg}")
        else:
            await message.reply("❌ Неверный формат времени. Используйте HH:MM (например, 09:00)")

async def admin_collect_news(message: types.Message):
    """Admin: manually trigger news collection"""
    if not is_admin(message.from_user.id):
        await message.reply("⛔ Доступ запрещен.")
        return
    
    await message.reply("🔄 Начинаю сбор новостей...")
    
    try:
        count = await run_scheduler_once(db)
        await message.reply(f"✅ Собрано {count} новых новостей")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

async def admin_news_stats(message: types.Message):
    """Admin: show news statistics"""
    if not is_admin(message.from_user.id):
        await message.reply("⛔ Доступ запрещен.")
        return
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM news_articles')
        total_news = cursor.fetchone()[0]
        
        if db.use_postgres:
            cursor.execute('SELECT COUNT(*) FROM news_articles WHERE DATE(published) = CURRENT_DATE')
            today_news = cursor.fetchone()[0]
            
            cursor.execute('SELECT category, COUNT(*) FROM news_articles GROUP BY category')
            by_category = cursor.fetchall()
            
            cursor.execute('SELECT COUNT(*) FROM user_interests')
            total_interests = cursor.fetchone()[0]
            
            categories_text = "\n".join([f"  {row[0]}: {row[1]}" for row in by_category])
        else:
            cursor.execute('SELECT COUNT(*) FROM news_articles WHERE date(published) = date("now")')
            today_news = cursor.fetchone()[0]
            
            cursor.execute('SELECT category, COUNT(*) FROM news_articles GROUP BY category')
            by_category = cursor.fetchall()
            
            cursor.execute('SELECT COUNT(*) FROM user_interests')
            total_interests = cursor.fetchone()[0]
            
            categories_text = "\n".join([f"  {row['category']}: {row[1]}" for row in by_category])
    
    await message.reply(
        f"📰 <b>Статистика новостей</b>\n\n"
        f"Всего новостей в базе: {total_news}\n"
        f"Сегодня добавлено: {today_news}\n"
        f"Всего подписок на категории: {total_interests}\n\n"
        f"<b>По категориям:</b>\n{categories_text}",
        parse_mode='HTML'
    )

# ========== AI IMAGE GENERATION & GPT-4 ==========

async def generate_image_handler(message: types.Message):
    """Generate image using DALL-E"""
    user_id = message.from_user.id
    if not await ensure_auth(message):
        return
    
    prompt = message.text.replace('/image', '').strip()
    if not prompt:
        await message.reply(
            "🎨 <b>Генерация изображений</b>\n\n"
            "Использование: /image &lt;описание&gt;\n\n"
            "Примеры:\n"
            "/image кот в космосе\n"
            "/image футуристический город\n"
            "/image логотип для кафе",
            parse_mode='HTML'
        )
        return
    
    # Check prompt length
    if len(prompt) > 1000:
        await message.reply("❌ Описание слишком длинное. Максимум 1000 символов.")
        return
    
    await message.reply("🎨 Генерирую изображение... Это может занять 10-30 секунд.")
    
    try:
        image_path = await asyncio.to_thread(image_gen.generate_image, prompt)
        
        if image_path:
            await bot.send_photo(
                message.chat.id,
                photo=FSInputFile(image_path),
                caption=f"🎨 <b>Сгенерировано по запросу:</b>\n{prompt}",
                parse_mode='HTML'
            )
            # Cleanup temp file
            import os
            os.unlink(image_path)
        else:
            await message.reply("❌ Не удалось сгенерировать изображение. Попробуйте другой запрос.")
    except Exception as e:
        logging.error(f"Error in image generation: {e}")
        await message.reply(f"❌ Ошибка при генерации: {e}")

async def deepseek_chat_handler(message: types.Message):
    """Chat with DeepSeek R1 (free) - advanced reasoning model"""
    user_id = message.from_user.id
    if not await ensure_auth(message):
        return
    
    user_input = message.text.replace('/gpt4', '').strip()
    if not user_input:
        await message.reply(
            "🧠 <b>DeepSeek R1 (Free)</b>\n\n"
            "Использование: /gpt4 &lt;вопрос&gt;\n\n"
            "DeepSeek R1 — бесплатная модель уровня GPT-4:\n"
            "• Сложный код и алгоритмы\n"
            "• Математика и логика\n"
            "• Анализ текста\n"
            "• Рассуждения (reasoning)\n\n"
            "⚡ Полностью бесплатно!\n"
            "Для обычных вопросов просто пишите без /gpt4",
            parse_mode='HTML'
        )
        return
    
    await message.reply("🧠 Думаю над ответом (DeepSeek R1)...")
    
    try:
        response = await asyncio.to_thread(deepseek_chat.simple_chat, user_input)
        
        # Save to chat history
        db.add_message(user_id, 'user', f'[GPT4] {user_input}')
        db.add_message(user_id, 'assistant', response)
        
        await message.reply(f"🧠 <b>DeepSeek R1:</b>\n{response}", parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error in DeepSeek chat: {e}")
        await message.reply(f"❌ Ошибка: {e}")

# ========== ADMIN MANAGEMENT COMMANDS ==========

async def admin_callback_handler(callback: types.CallbackQuery):
    """Handle admin panel callbacks"""
    data = callback.data or ''
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    await callback.answer()
    
    if data == "admin:users":
        await show_user_management(callback.message)
    elif data == "admin:admins":
        await show_admin_management(callback.message)
    elif data == "admin:banned":
        await show_banned_users(callback.message)
    elif data == "admin:stats":
        await show_detailed_stats(callback.message)
    elif data == "admin:broadcast":
        admin_states[user_id] = {'awaiting_broadcast': True}
        await callback.message.reply("📢 Введите текст для рассылки всем пользователям:")
    elif data == "admin:find_user":
        admin_states[user_id] = {'awaiting_user_search': True}
        await callback.message.reply("🔍 Введите ID пользователя или @username:")
    elif data.startswith("admin:ban:"):
        target_id = int(data.split(':')[2])
        admin_states[user_id] = {'awaiting_ban_reason': True, 'target_id': target_id}
        await callback.message.reply(f"🚫 Введите причину блокировки пользователя {target_id}:")
    elif data.startswith("admin:unban:"):
        target_id = int(data.split(':')[2])
        if db.unban_user(target_id):
            await callback.message.reply(f"✅ Пользователь {target_id} разблокирован")
        else:
            await callback.message.reply(f"❌ Не удалось разблокировать пользователя {target_id}")
    elif data.startswith("admin:make_admin:"):
        target_id = int(data.split(':')[2])
        admin_states[user_id] = {'awaiting_admin_role': True, 'target_id': target_id}
        await callback.message.reply(f"🛡️ Введите роль для админа (admin/superadmin) или 'отмена':")
    elif data.startswith("admin:remove_admin:"):
        target_id = int(data.split(':')[2])
        if target_id == ADMIN_ID:
            await callback.message.reply("❌ Нельзя удалить главного администратора")
        elif db.remove_admin(target_id):
            await callback.message.reply(f"✅ Администратор {target_id} удален")
        else:
            await callback.message.reply(f"❌ Не удалось удалить администратора {target_id}")
    elif data == "admin:back":
        await admin_panel(callback.message)

async def show_user_management(message: types.Message):
    """Show user management interface"""
    stats = db.get_admin_stats_extended()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Найти по ID", callback_data="admin:find_user")],
        [InlineKeyboardButton(text="🚫 Заблокировать", callback_data="admin:ban_user")],
        [InlineKeyboardButton(text="📋 Список заблокированных", callback_data="admin:banned")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")],
    ])
    
    await message.reply(
        f"👥 <b>Управление пользователями</b>\n\n"
        f"Всего пользователей: {stats['total_users']}\n"
        f"Заблокировано: {stats['total_banned']}\n\n"
        f"<i>Выберите действие:</i>",
        parse_mode='HTML',
        reply_markup=kb
    )

async def show_admin_management(message: types.Message):
    """Show admin management interface"""
    admins = db.get_all_admins()
    
    text = "🛡️ <b>Управление администраторами</b>\n\n"
    text += f"<b>Главный админ:</b> {ADMIN_ID}\n\n"
    
    if admins:
        text += "<b>Дополнительные админы:</b>\n"
        for admin in admins:
            text += f"• {admin['telegram_id']} (@{admin.get('username', 'N/A')}) - {admin.get('role', 'admin')}\n"
    else:
        text += "<i>Дополнительных админов нет</i>\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin:find_user")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")],
    ])
    
    await message.reply(text, parse_mode='HTML', reply_markup=kb)

async def show_banned_users(message: types.Message):
    """Show banned users list"""
    banned = db.get_all_banned()
    
    if not banned:
        await message.reply(
            "🚫 <b>Заблокированные пользователи</b>\n\n"
            "<i>Нет заблокированных пользователей</i>",
            parse_mode='HTML'
        )
        return
    
    text = "🚫 <b>Заблокированные пользователи</b>\n\n"
    for user in banned:
        name = user.get('first_name') or user.get('username') or f"ID:{user['telegram_id']}"
        admin_name = user.get('admin_name') or f"ID:{user['banned_by']}"
        text += (
            f"• <b>{name}</b>\n"
            f"  ID: {user['telegram_id']}\n"
            f"  Причина: {user.get('reason', 'Не указана')}\n"
            f"  Заблокировал: {admin_name}\n"
            f"  Дата: {str(user.get('banned_at', ''))[:10]}\n\n"
        )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")],
    ])
    
    await message.reply(text, parse_mode='HTML', reply_markup=kb)

async def show_detailed_stats(message: types.Message):
    """Show detailed statistics"""
    stats = db.get_admin_stats_extended()
    
    await message.reply(
        f"📊 <b>Детальная статистика</b>\n\n"
        f"<b>Пользователи:</b>\n"
        f"👥 Всего: {stats['total_users']}\n"
        f"🟢 Активных сегодня: {stats['active_today']}\n\n"
        f"<b>Данные:</b>\n"
        f"📇 Контактов: {stats['total_contacts']}\n"
        f"💬 Сообщений: {stats['total_messages']}\n\n"
        f"<b>Модерация:</b>\n"
        f"🛡️ Администраторов: {stats['total_admins']}\n"
        f"🚫 Заблокировано: {stats['total_banned']}\n",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")],
        ])
    )

async def handle_admin_text(message: types.Message):
    """Handle admin text inputs (ban reasons, broadcast, etc.)"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        return
    
    state = admin_states.get(user_id, {})
    
    # Handle broadcast
    if state.get('awaiting_broadcast'):
        admin_states.pop(user_id, None)
        text = message.text
        users = db.get_all_users()
        
        sent = 0
        failed = 0
        for user in users:
            try:
                await bot.send_message(
                    user['telegram_id'], 
                    f"📢 <b>Сообщение от администратора:</b>\n\n{text}",
                    parse_mode='HTML'
                )
                sent += 1
            except Exception as e:
                logging.error(f"Failed to send broadcast to {user['telegram_id']}: {e}")
                failed += 1
        
        await message.reply(f"✅ Рассылка завершена\nОтправлено: {sent}\nОшибок: {failed}")
        return
    
    # Handle ban reason
    if state.get('awaiting_ban_reason'):
        target_id = state['target_id']
        reason = message.text
        admin_states.pop(user_id, None)
        
        # Get target user info
        with db.get_connection() as conn:
            cursor = conn.cursor()
            db._execute(cursor, 'SELECT username, first_name FROM users WHERE telegram_id = ?', (target_id,))
            row = cursor.fetchone()
            username = row[0] if row else None
        
        if db.ban_user(target_id, username, reason, user_id):
            await message.reply(f"✅ Пользователь {target_id} заблокирован\nПричина: {reason}")
            try:
                await bot.send_message(
                    target_id,
                    f"⛔ <b>Вы заблокированы администратором</b>\n\nПричина: {reason}",
                    parse_mode='HTML'
                )
            except:
                pass
        else:
            await message.reply(f"❌ Не удалось заблокировать пользователя {target_id}")
        return
    
    # Handle admin role assignment
    if state.get('awaiting_admin_role'):
        target_id = state['target_id']
        role = message.text.lower().strip()
        admin_states.pop(user_id, None)
        
        if role in ['отмена', 'cancel', 'назад']:
            await message.reply("❌ Добавление администратора отменено")
            return
        
        if role not in ['admin', 'superadmin']:
            role = 'admin'
        
        # Get target user info
        with db.get_connection() as conn:
            cursor = conn.cursor()
            db._execute(cursor, 'SELECT username, first_name FROM users WHERE telegram_id = ?', (target_id,))
            row = cursor.fetchone()
            username = row[0] if row else None
        
        if db.add_admin(target_id, username, user_id, role):
            await message.reply(f"✅ Пользователь {target_id} назначен администратором\nРоль: {role}")
            try:
                await bot.send_message(
                    target_id,
                    f"🛡️ <b>Вас назначили администратором!</b>\n\nРоль: {role}\n\nИспользуйте /admin для доступа к панели",
                    parse_mode='HTML'
                )
            except:
                pass
        else:
            await message.reply(f"❌ Не удалось назначить администратора {target_id}")
        return
    
    # Handle user search
    if state.get('awaiting_user_search'):
        query = message.text.strip()
        admin_states.pop(user_id, None)
        
        # Try to find by ID or username
        target_id = None
        if query.isdigit():
            target_id = int(query)
        elif query.startswith('@'):
            username = query[1:]
            with db.get_connection() as conn:
                cursor = conn.cursor()
                db._execute(cursor, 'SELECT telegram_id FROM users WHERE username = ?', (username,))
                row = cursor.fetchone()
                if row:
                    target_id = row[0] if db.use_postgres else row['telegram_id']
        
        if not target_id:
            await message.reply(f"❌ Пользователь не найден: {query}")
            return
        
        # Show user info with actions
        await show_user_actions(message, target_id)
        return

async def show_user_actions(message: types.Message, target_id: int):
    """Show user info with action buttons"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        db._execute(cursor, 'SELECT * FROM users WHERE telegram_id = ?', (target_id,))
        user = cursor.fetchone()
        
        if not user:
            await message.reply(f"❌ Пользователь {target_id} не найден")
            return
        
        # Get stats
        stats = db.get_user_stats(target_id)
        is_user_admin = db.is_admin(target_id)
        is_user_banned = db.is_banned(target_id)
    
    # Build user info text
    if db.use_postgres:
        user_info = {
            'id': user[0], 'username': user[1], 'first_name': user[2],
            'last_name': user[3], 'created_at': user[4], 'last_active': user[5]
        }
    else:
        user_info = dict(user)
    
    text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"ID: <code>{user_info['id']}</code>\n"
        f"Username: @{user_info.get('username', 'нет')}\n"
        f"Имя: {user_info.get('first_name', 'нет')} {user_info.get('last_name', '')}\n"
        f"Статус: {'🛡️ Админ' if is_user_admin else '🚫 Заблокирован' if is_user_banned else '👤 Пользователь'}\n"
        f"Зарегистрирован: {str(user_info.get('created_at', ''))[:10]}\n"
        f"Последняя активность: {str(user_info.get('last_active', ''))[:10]}\n\n"
        f"📊 Сообщений: {stats['message_count']}\n"
        f"👤 Контактов: {stats['contact_count']}"
    )
    
    # Build action buttons
    buttons = []
    if not is_user_banned and target_id != ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"admin:ban:{target_id}")])
    if is_user_banned:
        buttons.append([InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"admin:unban:{target_id}")])
    if not is_user_admin and not is_user_banned:
        buttons.append([InlineKeyboardButton(text="➕ Сделать админом", callback_data=f"admin:make_admin:{target_id}")])
    if is_user_admin and target_id != ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="➖ Убрать из админов", callback_data=f"admin:remove_admin:{target_id}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply(text, parse_mode='HTML', reply_markup=kb)

# ========== CRYPTO COMMANDS ==========

async def crypto_menu(message: types.Message):
    """Show crypto menu"""
    if not await ensure_auth(message):
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Топ-10 по капитализации", callback_data="crypto:top")],
        [InlineKeyboardButton(text="🔥 Трендовые", callback_data="crypto:trending")],
        [InlineKeyboardButton(text="🔍 Поиск монеты", callback_data="crypto:search")],
        [InlineKeyboardButton(text="📈 BTC", callback_data="crypto:price:bitcoin"), 
         InlineKeyboardButton(text="📈 ETH", callback_data="crypto:price:ethereum")],
        [InlineKeyboardButton(text="📈 TON", callback_data="crypto:price:toncoin"), 
         InlineKeyboardButton(text="📈 SOL", callback_data="crypto:price:solana")],
        [InlineKeyboardButton(text="📊 Мой портфель", callback_data="crypto:portfolio")],
    ])
    
    await message.reply(
        "💰 <b>Криптовалюты</b>\n\n"
        "Отслеживайте цены в реальном времени:\n"
        "• Топ монет по капитализации\n"
        "• Трендовые криптовалюты\n"
        "• Поиск любой монеты\n"
        "• Ваш личный портфель\n\n"
        "<i>Выберите действие:</i>",
        parse_mode='HTML',
        reply_markup=kb
    )

async def crypto_portfolio(message: types.Message):
    """Show user's crypto portfolio"""
    if not await ensure_auth(message):
        return
    
    user_id = message.from_user.id
    portfolio = db.get_user_portfolio(user_id)
    
    if not portfolio:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить монету", callback_data="crypto:add")],
            [InlineKeyboardButton(text="💰 Меню крипто", callback_data="crypto:menu")],
        ])
        await message.reply(
            "📈 <b>Ваш портфель пуст</b>\n\n"
            "Добавьте криптовалюты чтобы отслеживать их стоимость.",
            parse_mode='HTML',
            reply_markup=kb
        )
        return
    
    # Get current prices
    coin_ids = [item['coin_id'] for item in portfolio]
    prices = crypto.get_multiple_prices(coin_ids)
    
    total_value = 0
    total_invested = 0
    text_parts = ["📈 <b>Ваш крипто-портфель</b>\n"]
    
    for item in portfolio:
        coin_id = item['coin_id']
        symbol = item['symbol']
        amount = item['amount']
        avg_price = item['avg_buy_price']
        
        if coin_id in prices:
            current_price = prices[coin_id]['price']
            value = amount * current_price
            invested = amount * avg_price if avg_price else 0
            pnl = value - invested
            pnl_percent = ((current_price - avg_price) / avg_price * 100) if avg_price else 0
            
            total_value += value
            total_invested += invested
            
            emoji = "🟢" if pnl >= 0 else "🔴"
            text_parts.append(
                f"\n<b>{symbol}</b> ({amount:.4f})\n"
                f"  Цена: {crypto.format_price(current_price)}\n"
                f"  Стоимость: {crypto.format_price(value)}\n"
                f"  {emoji} P&L: {pnl:+.2f}$ ({pnl_percent:+.2f}%)"
            )
        else:
            text_parts.append(f"\n<b>{symbol}</b>: данные недоступны")
    
    # Total P&L
    total_pnl = total_value - total_invested
    total_pnl_percent = ((total_value - total_invested) / total_invested * 100) if total_invested else 0
    emoji_total = "🟢" if total_pnl >= 0 else "🔴"
    
    text_parts.append(f"\n\n<b>📊 Итого:</b>")
    text_parts.append(f"  Стоимость: {crypto.format_price(total_value)}")
    text_parts.append(f"  {emoji_total} P&L: {total_pnl:+.2f}$ ({total_pnl_percent:+.2f}%)")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="crypto:add"),
         InlineKeyboardButton(text="📝 Изменить", callback_data="crypto:edit")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="crypto:portfolio"),
         InlineKeyboardButton(text="💰 Меню", callback_data="crypto:menu")],
    ])
    
    await message.reply("\n".join(text_parts), parse_mode='HTML', reply_markup=kb)

async def crypto_callback_handler(callback: types.CallbackQuery):
    """Handle crypto callbacks"""
    data = callback.data or ''
    user_id = callback.from_user.id
    
    await callback.answer()
    
    if data == "crypto:menu":
        await crypto_menu(callback.message)
        return
    
    if data == "crypto:portfolio":
        await crypto_portfolio(callback.message)
        return
    
    if data == "crypto:top":
        await callback.message.reply("⏳ Загружаю топ-10 монет...")
        coins = crypto.get_top_coins(10)
        
        if not coins:
            await callback.message.reply("❌ Не удалось загрузить данные. Попробуйте позже.")
            return
        
        text_parts = ["🏆 <b>Топ-10 криптовалют</b>\n"]
        for coin in coins:
            change_emoji = "🟢" if coin['change_24h'] and coin['change_24h'] > 0 else "🔴" if coin['change_24h'] and coin['change_24h'] < 0 else "⚪"
            text_parts.append(
                f"\n<b>#{coin['rank']} {coin['symbol']}</b> ({coin['name']})\n"
                f"  💰 Цена: {crypto.format_price(coin['price'])}\n"
                f"  {change_emoji} 24ч: {coin['change_24h']:+.2f}%\n"
                f"  📊 Капитализация: {crypto.format_price(coin['market_cap'])}"
            )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Меню", callback_data="crypto:menu")],
        ])
        await callback.message.reply("\n".join(text_parts), parse_mode='HTML', reply_markup=kb)
        return
    
    if data == "crypto:trending":
        await callback.message.reply("⏳ Загружаю трендовые монеты...")
        coins = crypto.get_trending()
        
        if not coins:
            await callback.message.reply("❌ Не удалось загрузить данные. Попробуйте позже.")
            return
        
        text_parts = ["🔥 <b>Трендовые криптовалюты</b>\n"]
        for coin in coins:
            text_parts.append(
                f"\n<b>{coin['symbol']}</b> - {coin['name']}\n"
                f"  📊 Ранг: #{coin['market_cap_rank']}"
            )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Меню", callback_data="crypto:menu")],
        ])
        await callback.message.reply("\n".join(text_parts), parse_mode='HTML', reply_markup=kb)
        return
    
    if data == "crypto:search":
        user_states[user_id] = {'awaiting_crypto_search': True}
        await callback.message.reply("🔍 Введите название или символ монеты (например: BTC, bitcoin, Ethereum):")
        return
    
    if data == "crypto:add":
        user_states[user_id] = {'awaiting_crypto_add': True}
        await callback.message.reply(
            "➕ <b>Добавление в портфель</b>\n\n"
            "Введите данные в формате:\n"
            "<code>SYMBOL КОЛИЧЕСТВО ЦЕНА_ПОКУПКИ</code>\n\n"
            "Примеры:\n"
            "<code>BTC 0.5 45000</code>\n"
            "<code>ETH 2.5 3000</code>\n\n"
            "Если не помните цену покупки, введите 0",
            parse_mode='HTML'
        )
        return
    
    if data == "crypto:edit":
        user_states[user_id] = {'awaiting_crypto_edit': True}
        await callback.message.reply(
            "📝 <b>Изменение в портфеле</b>\n\n"
            "Введите данные в формате:\n"
            "<code>SYMBOL НОВОЕ_КОЛИЧЕСТВО НОВАЯ_ЦЕНА</code>\n\n"
            "Или для удаления: <code>SYMBOL 0 0</code>",
            parse_mode='HTML'
        )
        return
    
    if data.startswith("crypto:price:"):
        coin_id = data.split(':')[2]
        await callback.message.reply(f"⏳ Загружаю цену {coin_id}...")
        
        price_data = crypto.get_price(coin_id)
        if not price_data:
            await callback.message.reply("❌ Не удалось получить данные. Попробуйте позже.")
            return
        
        if 'error' in price_data:
            await callback.message.reply("⏳ Превышен лимит запросов. Попробуйте через минуту.")
            return
        
        change_emoji = "🟢" if price_data['change_24h'] > 0 else "🔴" if price_data['change_24h'] < 0 else "⚪"
        
        text = (
            f"💰 <b>{coin_id.upper()}</b>\n\n"
            f"Цена: {crypto.format_price(price_data['price'])}\n"
            f"{change_emoji} 24ч: {price_data['change_24h']:+.2f}%\n"
            f"📊 Капитализация: {crypto.format_price(price_data['market_cap'])}\n"
            f"📈 Объем 24ч: {crypto.format_price(price_data['volume_24h'])}"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ В портфель", callback_data=f"crypto:add_quick:{coin_id}"),
             InlineKeyboardButton(text="🔄 Обновить", callback_data=f"crypto:price:{coin_id}")],
            [InlineKeyboardButton(text="💰 Меню", callback_data="crypto:menu")],
        ])
        await callback.message.reply(text, parse_mode='HTML', reply_markup=kb)
        return
    
    if data.startswith("crypto:add_quick:"):
        coin_id = data.split(':')[2]
        user_states[user_id] = {'awaiting_crypto_add_quick': True, 'coin_id': coin_id}
        await callback.message.reply(
            f"➕ <b>Добавление {coin_id.upper()}</b>\n\n"
            f"Введите количество и цену покупки:\n"
            f"<code>КОЛИЧЕСТВО ЦЕНА</code>\n\n"
            f"Пример: <code>0.5 45000</code>",
            parse_mode='HTML'
        )
        return

async def handle_crypto_text(message: types.Message):
    """Handle crypto text inputs"""
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    # Handle crypto search
    if state.get('awaiting_crypto_search'):
        query = message.text.strip()
        user_states.pop(user_id, None)
        
        await message.reply(f"🔍 Ищу {query}...")
        coin = crypto.search_coin(query)
        
        if not coin:
            await message.reply(f"❌ Монета '{query}' не найдена. Попробуйте другой запрос.")
            return
        
        # Get price
        price_data = crypto.get_price(coin['id'])
        if price_data and 'error' not in price_data:
            change_emoji = "🟢" if price_data['change_24h'] > 0 else "🔴" if price_data['change_24h'] < 0 else "⚪"
            text = (
                f"💰 <b>{coin['symbol']}</b> - {coin['name']}\n\n"
                f"Цена: {crypto.format_price(price_data['price'])}\n"
                f"{change_emoji} 24ч: {price_data['change_24h']:+.2f}%\n"
                f"📊 Капитализация: {crypto.format_price(price_data['market_cap'])}"
            )
        else:
            text = f"💰 <b>{coin['symbol']}</b> - {coin['name']}\n\n<i>Данные о цене временно недоступны</i>"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ В портфель", callback_data=f"crypto:add_quick:{coin['id']}")],
            [InlineKeyboardButton(text="💰 Меню", callback_data="crypto:menu")],
        ])
        await message.reply(text, parse_mode='HTML', reply_markup=kb)
        return
    
    # Handle add to portfolio
    if state.get('awaiting_crypto_add'):
        text = message.text.strip()
        user_states.pop(user_id, None)
        
        parts = text.split()
        if len(parts) < 2:
            await message.reply("❌ Неверный формат. Используйте: SYMBOL КОЛИЧЕСТВО ЦЕНА_ПОКУПКИ")
            return
        
        symbol = parts[0].upper()
        try:
            amount = float(parts[1])
            avg_price = float(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            await message.reply("❌ Неверные числа. Проверьте формат.")
            return
        
        # Search coin
        coin = crypto.search_coin(symbol)
        if not coin:
            await message.reply(f"❌ Монета '{symbol}' не найдена.")
            return
        
        # Add to portfolio
        if db.add_crypto_to_portfolio(user_id, coin['id'], coin['symbol'], amount, avg_price):
            await message.reply(
                f"✅ <b>{coin['symbol']}</b> добавлен в портфель!\n"
                f"Количество: {amount}\n"
                f"Цена покупки: {crypto.format_price(avg_price) if avg_price else 'Не указана'}",
                parse_mode='HTML'
            )
        else:
            await message.reply("❌ Ошибка при добавлении. Попробуйте позже.")
        return
    
    # Handle quick add
    if state.get('awaiting_crypto_add_quick'):
        text = message.text.strip()
        coin_id = state.get('coin_id')
        user_states.pop(user_id, None)
        
        parts = text.split()
        if len(parts) < 1:
            await message.reply("❌ Введите количество и цену (опционально)")
            return
        
        try:
            amount = float(parts[0])
            avg_price = float(parts[1]) if len(parts) > 1 else 0
        except ValueError:
            await message.reply("❌ Неверные числа")
            return
        
        # Get coin info
        price_data = crypto.get_price(coin_id)
        symbol = coin_id.upper()
        
        if db.add_crypto_to_portfolio(user_id, coin_id, symbol, amount, avg_price):
            await message.reply(
                f"✅ <b>{symbol}</b> добавлен в портфель!\n"
                f"Количество: {amount}",
                parse_mode='HTML'
            )
        else:
            await message.reply("❌ Ошибка при добавлении")
        return
    
    # Handle edit portfolio
    if state.get('awaiting_crypto_edit'):
        text = message.text.strip()
        user_states.pop(user_id, None)
        
        parts = text.split()
        if len(parts) < 3:
            await message.reply("❌ Неверный формат. Используйте: SYMBOL НОВОЕ_КОЛИЧЕСТВО НОВАЯ_ЦЕНА")
            return
        
        symbol = parts[0].upper()
        try:
            amount = float(parts[1])
            avg_price = float(parts[2])
        except ValueError:
            await message.reply("❌ Неверные числа")
            return
        
        # Search coin
        coin = crypto.search_coin(symbol)
        if not coin:
            await message.reply(f"❌ Монета '{symbol}' не найдена в вашем портфеле.")
            return
        
        coin_id = coin['id']
        
        # Remove if amount is 0
        if amount == 0:
            if db.remove_crypto_from_portfolio(user_id, coin_id):
                await message.reply(f"✅ <b>{symbol}</b> удален из портфеля", parse_mode='HTML')
            else:
                await message.reply("❌ Ошибка при удалении")
            return
        
        # Update
        if db.add_crypto_to_portfolio(user_id, coin_id, coin['symbol'], amount, avg_price):
            await message.reply(
                f"✅ <b>{symbol}</b> обновлен!\n"
                f"Новое количество: {amount}",
                parse_mode='HTML'
            )
        else:
            await message.reply("❌ Ошибка при обновлении")
        return

async def main():
    # Initialize scheduler
    scheduler = NewsScheduler(bot, db)
    
    # Start scheduler in background
    scheduler_task = asyncio.create_task(scheduler.start())
    
    # Register handlers
    dp.message.register(send_welcome, Command(commands=['start']))
    dp.message.register(weather_bishkek, Command(commands=['weather_bishkek']))
    dp.message.register(weather_moscow, Command(commands=['weather_moscow']))
    dp.message.register(weather_issykkul, Command(commands=['weather_issykkul']))
    dp.message.register(weather_bokonbaevo, Command(commands=['weather_bokonbaevo']))
    dp.message.register(weather_ton, Command(commands=['weather_ton']))
    dp.message.register(currency, Command(commands=['currency']))
    dp.message.register(news_kyrgyzstan, Command(commands=['news_kyrgyzstan']))
    dp.message.register(voice_handler, Command(commands=['voice']))
    dp.message.register(toggle_voice, Command(commands=['toggle_voice']))
    dp.message.register(clear_history, Command(commands=['clear_history']))
    dp.message.register(user_stats, Command(commands=['stats']))
    # News digest commands
    dp.message.register(show_interests, Command(commands=['interests']))
    dp.message.register(get_digest, Command(commands=['digest']))
    dp.message.register(schedule_digest, Command(commands=['schedule']))
    # Add interest handlers for each category
    for cat in ['tech', 'ai', 'science', 'space', 'finance', 'kyrgyzstan', 'world', 'sports', 'other']:
        dp.message.register(add_interest_handler, Command(commands=[f'add_{cat}']))
        dp.message.register(remove_interest_handler, Command(commands=[f'remove_{cat}']))
    # AI Image & GPT-4
    dp.message.register(generate_image_handler, Command(commands=['image']))
    dp.message.register(deepseek_chat_handler, Command(commands=['gpt4']))
    # Admin commands
    dp.message.register(admin_panel, Command(commands=['admin']))
    dp.message.register(broadcast_message, Command(commands=['broadcast']))
    dp.message.register(user_info, Command(commands=['user_info']))
    dp.message.register(admin_collect_news, Command(commands=['collect_news']))
    dp.message.register(admin_news_stats, Command(commands=['news_stats']))
    # Voice messages handler
    dp.message.register(handle_voice_message, lambda msg: msg.voice is not None)
    # Admin callback handler
    dp.callback_query.register(admin_callback_handler, lambda c: c.data and c.data.startswith('admin:'))
    # Admin text handler (for ban reasons, broadcast, etc.)
    dp.message.register(handle_admin_text, lambda msg: is_admin(msg.from_user.id) and msg.from_user.id in admin_states)
    # Crypto callback handler
    dp.callback_query.register(crypto_callback_handler, lambda c: c.data and c.data.startswith('crypto:'))
    # Crypto text handler
    dp.message.register(handle_crypto_text, lambda msg: msg.from_user.id in user_states and any(k in user_states.get(msg.from_user.id, {}) for k in ['awaiting_crypto_search', 'awaiting_crypto_add', 'awaiting_crypto_add_quick', 'awaiting_crypto_edit']))
    # Text messages
    dp.message.register(handle_text)
    dp.callback_query.register(contact_callback_handler)
    
    logging.info("Бот запущен и готов к обработке сообщений.")
    
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.stop()
        scheduler_task.cancel()

if __name__ == '__main__':
    # Запускаем только на Railway (проверяем переменную окружения Railway)
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        asyncio.run(main())
    else:
        logging.warning("Бот не запущен: запуск разрешён только на Railway (переменная RAILWAY_ENVIRONMENT не найдена).")
        print("[STOP] Bot stopped locally. Deploy to Railway to run.")