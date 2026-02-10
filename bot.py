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
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # Установи свой Telegram ID в Railway Variables

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id == ADMIN_ID

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
            "💰 /currency - Курс валют\n\n"
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

async def admin_panel(message: types.Message):
    """Admin panel with full statistics"""
    if not is_admin(message.from_user.id):
        await message.reply("⛔ Доступ запрещен.")
        return
    
    stats = db.get_admin_stats()
    await message.reply(
        f"👑 <b>Панель администратора</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"🟢 Активных сегодня: {stats['active_today']}\n"
        f"📇 Всего контактов: {stats['total_contacts']}\n"
        f"💬 Всего сообщений: {stats['total_messages']}\n\n"
        f"<b>Команды:</b>\n"
        f"/broadcast &lt;текст&gt; - Рассылка всем\n"
        f"/user_info &lt;id&gt; - Инфо о пользователе",
        parse_mode='HTML'
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