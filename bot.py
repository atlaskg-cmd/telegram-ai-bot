import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
import requests
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not API_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Please set TELEGRAM_API_TOKEN and OPENROUTER_API_KEY environment variables.")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Function to query OpenRouter API
def query_openrouter(prompt):
    logging.info(f"Отправка запроса к OpenRouter API: {prompt}")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "xiaomi/mimo-v2-flash:free",
        "messages": [{"role": "user", "content": f"Ответь на русском языке: {prompt}"}],
        "max_tokens": 100
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        logging.info(f"Ответ от OpenRouter API: {response.status_code} {response.text}")
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            else:
                return "Ошибка: пустой ответ от API"
        else:
            return f"Ошибка: {response.status_code} {response.text}"
    except Exception as e:
        logging.error(f"Ошибка при запросе к OpenRouter API: {e}")
        return "Ошибка при подключении к OpenRouter API. Попробуйте позже."

# Command handler for /start
async def send_welcome(message: types.Message):
    logging.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.reply("Привет! Я ИИ-бот. Задай мне любой вопрос, и я постараюсь ответить.")

# Message handler for user queries
async def handle_query(message: types.Message):
    user_input = message.text
    logging.info(f"Получено сообщение от пользователя {message.from_user.id}: {user_input}")
    await message.reply("Обрабатываю ваш запрос...")
    response = query_openrouter(user_input)
    await message.reply(response)

async def main():
    dp.message.register(send_welcome, Command(commands=['start']))
    dp.message.register(handle_query)
    logging.info("Бот запущен и готов к обработке сообщений.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())