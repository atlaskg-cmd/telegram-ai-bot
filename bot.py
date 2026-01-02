import logging
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
import requests
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize bot and dispatcher
API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN", "7968782605:AAEyELGMhUCMwzHH7FglYs9oL4Hi0Ew7CkQ")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", config.get("openrouter_api_key"))
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", config.get("weather_api_key", "YOUR_OPENWEATHERMAP_API_KEY"))

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Dictionary to store conversation history for each user
user_histories = {}

# Function to query OpenRouter API
def query_deepseek(messages):
    if not OPENROUTER_API_KEY:
        return "OPENROUTER_API_KEY не установлен. Установите переменную окружения OPENROUTER_API_KEY."
    logging.info(f"Отправка запроса к OpenRouter API с историей: {messages}")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": config.get("default_model", "xiaomi/mimo-v2-flash:free"),
        "messages": messages,
        "max_tokens": 1000
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        logging.info(f"Ответ от OpenRouter API: {response.status_code} {response.text}")
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Ошибка: {response.status_code} {response.text}"
    except Exception as e:
        logging.error(f"Ошибка при запросе к OpenRouter API: {e}")
        return "Ошибка при подключении к OpenRouter API. Попробуйте позже."

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
            # Decode weathercode to description
            descriptions = {
                0: "ясно", 1: "преимущественно ясно", 2: "переменная облачность", 3: "пасмурно",
                45: "туман", 48: "изморось", 51: "мелкий дождь", 53: "дождь", 55: "сильный дождь",
                56: "ледяной дождь", 57: "сильный ледяной дождь", 61: "небольшой дождь", 63: "дождь", 65: "сильный дождь",
                66: "ледяной дождь", 67: "сильный ледяной дождь", 71: "небольшой снег", 73: "снег", 75: "сильный снег",
                77: "снежные зерна", 80: "небольшой дождь", 81: "дождь", 82: "сильный дождь",
                85: "небольшой снег", 86: "сильный снег", 95: "гроза", 96: "гроза с градом", 99: "сильная гроза с градом"
            }
            description = descriptions.get(weathercode, "неизвестно")
            return f"Погода в {city}: {temp}°C, {description}"
        else:
            return "Не удалось получить данные о погоде."
    except Exception as e:
        logging.error(f"Ошибка при получении погоды: {e}")
        return "Ошибка при подключении к API погоды."

# Function to get currency rates
def get_currency():
    url = config["currency_api_url"]
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            usd_to_kgs = data['rates']['KGS']
            usd_to_rub = data['rates']['RUB']
            return f"Курс USD: KGS {usd_to_kgs:.2f}, RUB {usd_to_rub:.2f}"
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
                        recent_news.append(f"{title}\n{url}")
                except ValueError:
                    continue  # Skip if date parsing fails
            if len(recent_news) >= 5:
                break
        if not recent_news:
            return "Нет новостей за последние 3 дня."
        return "\n\n".join(recent_news)
    except Exception as e:
        logging.error(f"Ошибка при получении новостей: {e}")
        return "Ошибка при подключении к RSS."

# Command handler for /start
async def send_welcome(message: types.Message):
    logging.info(f"Получена команда /start от пользователя {message.from_user.id}")
    menu = (
        "Привет! Я ИИ-бот.\n"
        "Доступные команды:\n"
        "/weather_bishkek - Погода в Бишкеке\n"
        "/weather_moscow - Погода в Москве\n"
        "/weather_issykkul - Погода в Иссык-Куле\n"
        "/weather_bokonbaevo - Погода в Боконбаево\n"
        "/weather_ton - Погода в Тоне\n"
        "/currency - Курс валют\n"
        "/news_kyrgyzstan - Новости Киргизстана за последние 3 дня\n"
        "Просто напишите свой вопрос, и я отвечу!\n"
    )
    await message.reply(menu)

# Handler for weather in Bishkek
async def weather_bishkek(message: types.Message):
    logging.info(f"Получена команда /weather_bishkek от пользователя {message.from_user.id}")
    await message.reply("Получаю погоду в Бишкеке...")
    response = get_weather("Bishkek")
    await message.reply(response)

# Handler for weather in Moscow
async def weather_moscow(message: types.Message):
    logging.info(f"Получена команда /weather_moscow от пользователя {message.from_user.id}")
    await message.reply("Получаю погоду в Москве...")
    response = get_weather("Moscow")
    await message.reply(response)

# Handler for weather in Issyk-Kul
async def weather_issykkul(message: types.Message):
    logging.info(f"Получена команда /weather_issykkul от пользователя {message.from_user.id}")
    await message.reply("Получаю погоду в Иссык-Куле...")
    response = get_weather("Issyk-Kul")
    await message.reply(response)

# Handler for weather in Bokonbaevo
async def weather_bokonbaevo(message: types.Message):
    logging.info(f"Получена команда /weather_bokonbaevo от пользователя {message.from_user.id}")
    await message.reply("Получаю погоду в Боконбаево...")
    response = get_weather("Bokonbaevo")
    await message.reply(response)

# Handler for weather in Ton
async def weather_ton(message: types.Message):
    logging.info(f"Получена команда /weather_ton от пользователя {message.from_user.id}")
    await message.reply("Получаю погоду в Тоне...")
    response = get_weather("Ton")
    await message.reply(response)

# Handler for currency
async def currency(message: types.Message):
    logging.info(f"Получена команда /currency от пользователя {message.from_user.id}")
    await message.reply("Получаю курс валют...")
    response = get_currency()
    await message.reply(response)

# Handler for news Kyrgyzstan
async def news_kyrgyzstan(message: types.Message):
    logging.info(f"Получена команда /news_kyrgyzstan от пользователя {message.from_user.id}")
    await message.reply("Получаю новости Киргизстана за последние 3 дня...")
    response = get_news_kyrgyzstan()
    await message.reply(response)

# Handler for text messages (questions)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    user_input = message.text
    logging.info(f"Получен текст от пользователя {user_id}: {user_input}")

    # Initialize history if not exists
    if user_id not in user_histories:
        user_histories[user_id] = []

    # Add user message to history
    user_histories[user_id].append({"role": "user", "content": user_input})

    # Limit history to last 20 messages to avoid exceeding limits
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

    await message.reply("Обрабатываю ваш вопрос...")
    response = query_deepseek(user_histories[user_id])
    await message.reply(response)

    # Add assistant response to history
    user_histories[user_id].append({"role": "assistant", "content": response})

async def main():
    dp.message.register(send_welcome, Command(commands=['start']))
    dp.message.register(weather_bishkek, Command(commands=['weather_bishkek']))
    dp.message.register(weather_moscow, Command(commands=['weather_moscow']))
    dp.message.register(weather_issykkul, Command(commands=['weather_issykkul']))
    dp.message.register(weather_bokonbaevo, Command(commands=['weather_bokonbaevo']))
    dp.message.register(weather_ton, Command(commands=['weather_ton']))
    dp.message.register(currency, Command(commands=['currency']))
    dp.message.register(news_kyrgyzstan, Command(commands=['news_kyrgyzstan']))
    dp.message.register(handle_text)
    logging.info("Бот запущен и готов к обработке сообщений.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())