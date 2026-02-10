# Telegram AI Bot

Version: 2.0.0

This is a Telegram bot that uses AI to answer user questions via OpenRouter API, and provides weather, currency information, news, and contacts.

## Setup

1. Clone the repository.
2. Create a virtual environment: `python -m venv .venv`
3. Activate it: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Configure API keys (choose one method):
   
   **For Railway (Production - Recommended):**
   - Set environment variables in Railway Dashboard:
     - `TELEGRAM_API_TOKEN`: Your Telegram Bot API token from BotFather.
     - `OPENROUTER_API_KEY`: Your OpenRouter API key.
     - `WEATHER_API_KEY`: Your OpenWeatherMap API key.
     - `ADMIN_ID`: Your Telegram numeric ID (for admin panel access).
   - These variables override config.json and are secure (not visible in GitHub).
   - Get your Telegram ID: message `@userinfobot` on Telegram.
   
   **For Local Development (not recommended for this bot):**
   - Copy `config.example.json` to `config.json`.
   - Edit `config.json` and replace placeholder API keys with your actual keys.

6. Deploy to Railway: Push to GitHub, Railway auto-deploys.

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
- **Edge-TTS**: High-quality voice responses using Microsoft Edge voices (ru-RU-SvetlanaNeural).
- **Voice Recognition**: Send voice messages and bot transcribes + responds (Whisper API).
- **AI News Digest**: Personalized news from 20+ RSS sources with sentiment analysis.
- **Admin Panel**: Statistics, broadcast messages, user info.
- Contacts: View and search contacts with inline keyboard.
- Reply keyboard for quick access to commands.
- Password protection for bot access.

## Changelog

### Version 2.0.0 - AI News Digest
- **Added:** News aggregator with 20+ RSS sources (Tech, AI, Science, Space, Finance, Kyrgyzstan, World, Sports).
- **Added:** AI sentiment analysis for each news (positive/negative/neutral).
- **Added:** Personalized news feeds - users choose interests.
- **Added:** Scheduled digest delivery every day.
- **Added:** Commands: `/interests`, `/digest`, `/schedule`.
- **Added:** Admin commands: `/collect_news`, `/news_stats`.

### Version 1.5.0
- **Added:** Admin panel (`/admin`, `/broadcast`, `/user_info`) - only for admin.
- **Added:** Voice recognition - transcribe voice messages using Whisper API.
- **Added:** Webhook support for production (automatic on Railway).

### Version 1.4.0
- **Added:** Edge-TTS integration - high-quality voice synthesis using Microsoft Edge voices.
- **Changed:** Voice responses now use `ru-RU-SvetlanaNeural` (female) by default for more natural sound.
- **Changed:** Fallback to gTTS if Edge-TTS is unavailable.

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
