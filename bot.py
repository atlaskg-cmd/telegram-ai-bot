import logging
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize bot and dispatcher
API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN", "7968782605:AAEyELGMhUCMwzHH7FglYs9oL4Hi0Ew7CkQ")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", config.get("weather_api_key", "YOUR_OPENWEATHERMAP_API_KEY"))

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Function to query OpenRouter API
def query_deepseek(prompt):
    logging.info(f"Отправка запроса к OpenRouter API: {prompt}")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "xiaomi/mimo-v2-flash:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100
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
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            description = data['weather'][0]['description']
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

# Command handler for /start
async def send_welcome(message: types.Message):
    logging.info(f"Получена команда /start от пользователя {message.from_user.id}")
    menu = (
        "Привет! Я ИИ-бот.\n"
        "Доступные команды:\n"
        "/weather_bishkek - Погода в Бишкеке\n"
        "/weather_moscow - Погода в Москве\n"
        "/currency - Курс валют\n"
        "Или просто задай мне любой вопрос!"
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

# Handler for currency
async def currency(message: types.Message):
    logging.info(f"Получена команда /currency от пользователя {message.from_user.id}")
    await message.reply("Получаю курс валют...")
    response = get_currency()
    await message.reply(response)

# Message handler for user queries
async def handle_query(message: types.Message):
    user_input = message.text
    logging.info(f"Получено сообщение от пользователя {message.from_user.id}: {user_input}")
    await message.reply("Обрабатываю ваш запрос...")
    response = query_deepseek(user_input)
    await message.reply(response)

async def main():
    dp.message.register(send_welcome, Command(commands=['start']))
    dp.message.register(weather_bishkek, Command(commands=['weather_bishkek']))
    dp.message.register(weather_moscow, Command(commands=['weather_moscow']))
    dp.message.register(currency, Command(commands=['currency']))
    dp.message.register(handle_query)
    logging.info("Бот запущен и готов к обработке сообщений.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())