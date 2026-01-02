import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
import requests
import os
import json

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    logging.error("config.json not found. Using default settings.")
    config = {
        "models": ["xiaomi/mimo-v2-flash:free"],
        "default_model": "xiaomi/mimo-v2-flash:free",
        "max_tokens_base": 100,
        "max_tokens_scale_factor": 0.5,
        "retry_attempts": 3,
        "language": "ru",
        "fallback_on_error": True
    }

# Language prompts
language_prompts = {
    "ru": "Ответь на русском языке: ",
    "en": "Answer in English: ",
    "auto": ""  # No forced language
}

# Initialize bot and dispatcher
API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not API_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Please set TELEGRAM_API_TOKEN and OPENROUTER_API_KEY environment variables.")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Function to query OpenRouter API with adaptive settings
def query_openrouter(prompt):
    logging.info(f"Отправка запроса к OpenRouter API: {prompt}")

    # Calculate max_tokens based on input length
    max_tokens = int(config["max_tokens_base"] + len(prompt) * config["max_tokens_scale_factor"])

    # Get language instruction
    lang_key = config.get("language", "ru")
    lang_prompt = language_prompts.get(lang_key, "")
    full_prompt = f"{lang_prompt}{prompt}"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    models = config["models"]
    start_index = models.index(config["default_model"]) if config["default_model"] in models else 0
    retry_attempts = config["retry_attempts"]
    fallback = config["fallback_on_error"]

    for i in range(len(models)):
        model = models[(start_index + i) % len(models)]
        logging.info(f"Trying model: {model}")
        for attempt in range(retry_attempts):
            try:
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": full_prompt}],
                    "max_tokens": max_tokens
                }
                response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=30)
                logging.info(f"Ответ от OpenRouter API: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and result["choices"]:
                        return result["choices"][0]["message"]["content"]
                    else:
                        logging.warning("Empty response from API")
                        continue
                else:
                    logging.warning(f"API error: {response.status_code} {response.text}")
                    continue
            except requests.exceptions.RequestException as e:
                logging.error(f"Request exception: {e}")
                continue
        if not fallback:
            break
    return "Ошибка: не удалось получить ответ от API после всех попыток. Попробуйте позже."

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