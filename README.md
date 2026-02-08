# Telegram AI Bot

Version: 1.3.0

This is a Telegram bot that uses AI to answer user questions via OpenRouter API, and provides weather, currency information, news, and contacts.

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
- Answers any user message using AI via OpenRouter API.
- /weather_bishkek: Get weather in Bishkek.
- /weather_moscow: Get weather in Moscow.
- /weather_issykkul: Get weather in Issyk-Kul.
- /weather_bokonbaevo: Get weather in Bokonbaevo.
- /weather_ton: Get weather in Ton.
- /currency: Get USD exchange rates to KGS and RUB.
- /news_kyrgyzstan: Get latest news from Kyrgyzstan (last 3 days).
- /toggle_voice: Toggle voice response mode.
- /voice [question]: Get voice response for a question.
- Contacts: View and search contacts with inline keyboard.
- Reply keyboard for quick access to commands.
- Password protection for bot access.

## Changelog

### Version 1.3.0
- **Changed:** Updated AI model to `arcee-ai/trinity-large-preview:free` (free model).
- **Changed:** Fixed OpenRouter API response parsing to correctly extract AI message content.
- **Added:** News functionality - get latest news from Kyrgyzstan via RSS (kaktus.media).
- **Added:** Contacts feature - view and search contacts with inline keyboard.
- **Added:** Voice response support using Google Text-to-Speech (gTTS).
- **Added:** Voice mode toggle for automatic voice responses.
- **Added:** Password protection (`AUTH_PASSWORD = "1916"`) for bot access.
- **Added:** Extended weather locations - Issyk-Kul, Bokonbaevo, Ton.
- **Added:** Reply keyboard with quick buttons for weather, currency, news, contacts, and voice mode.

### Version 1.2.0
- Added weather functionality for Bishkek and Moscow using OpenWeatherMap API.
- Added currency exchange rates (USD to KGS and RUB) using ExchangeRate API.
- Updated bot menu with available commands.
- Simplified AI query function for better reliability.
- Added configuration options for weather and currency APIs in config.json.

### Version 1.1.0
- Initial release with AI question answering via OpenRouter API.
