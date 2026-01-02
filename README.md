# Telegram AI Bot

This is a Telegram bot that uses AI to answer user questions via OpenRouter API.

## Setup

1. Clone the repository.
2. Create a virtual environment: `python -m venv .venv`
3. Activate it: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Set environment variables:
   - `TELEGRAM_API_TOKEN`: Your Telegram Bot API token from BotFather.
   - `OPENROUTER_API_KEY`: Your OpenRouter API key.
6. Run the bot: `python bot.py`

## Features

- Responds to /start command.
- Answers any user message using AI.