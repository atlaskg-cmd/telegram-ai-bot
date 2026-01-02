# Telegram AI Bot

Version: 1.2.0

This is a Telegram bot that uses AI to answer user questions via OpenRouter API, and provides weather and currency information.

## Setup

1. Clone the repository.
2. Create a virtual environment: `python -m venv .venv`
3. Activate it: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Configure API keys:
   - Copy `config.example.json` to `config.json`.
   - Edit `config.json` and replace placeholder API keys with your actual keys:
     - `openrouter_api_key`: Your OpenRouter API key.
     - `weather_api_key`: Your OpenWeatherMap API key.
   - Alternatively, set environment variables (they will override config.json):
     - `TELEGRAM_API_TOKEN`: Your Telegram Bot API token from BotFather.
     - `OPENROUTER_API_KEY`: Your OpenRouter API key.
     - `WEATHER_API_KEY`: Your OpenWeatherMap API key.
6. Run the bot: `python bot.py`

## Features

- Responds to /start command with menu.
- Answers any user message using AI.
- /weather_bishkek: Get weather in Bishkek.
- /weather_moscow: Get weather in Moscow.
- /currency: Get USD exchange rates to KGS and RUB.

## Changelog

### Version 1.2.0
- Added weather functionality for Bishkek and Moscow using OpenWeatherMap API.
- Added currency exchange rates (USD to KGS and RUB) using ExchangeRate API.
- Updated bot menu with available commands.
- Simplified AI query function for better reliability.
- Added configuration options for weather and currency APIs in config.json.

### Version 1.1.0
- Initial release with AI question answering via OpenRouter API.