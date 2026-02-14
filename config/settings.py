"""
Configuration settings for both Telegram and WhatsApp bots.
Uses environment variables for sensitive data.
"""
import os
from dataclasses import dataclass


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    API_TOKEN: str = os.environ.get("TELEGRAM_API_TOKEN", "")
    ENABLED: bool = bool(API_TOKEN)


@dataclass
class WhatsAppConfig:
    """WhatsApp (Green API) configuration."""
    # Get from https://console.green-api.com/
    API_ID: str = os.environ.get("GREEN_API_ID", "")
    API_TOKEN: str = os.environ.get("GREEN_API_TOKEN", "")
    ENABLED: bool = bool(API_ID and API_TOKEN)


@dataclass
class AppConfig:
    """Application configuration."""
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    
    # Feature flags
    ENABLE_TELEGRAM: bool = True
    ENABLE_WHATSAPP: bool = True
    
    # API URLs
    EXCHANGE_RATE_API: str = "https://api.exchangerate-api.com/v4/latest/"


# Global config instances
telegram_config = TelegramConfig()
whatsapp_config = WhatsAppConfig()
app_config = AppConfig()


# Validate configuration
def validate_config():
    """Check if required environment variables are set."""
    errors = []
    
    if not telegram_config.ENABLED:
        errors.append("TELEGRAM_API_TOKEN not set - Telegram bot disabled")
    
    if not whatsapp_config.ENABLED:
        errors.append("GREEN_API_ID or GREEN_API_TOKEN not set - WhatsApp bot disabled")
    
    if errors:
        print("⚠️  Configuration warnings:")
        for error in errors:
            print(f"  - {error}")
        print("\nTo enable all features, set these environment variables:")
        print("  export TELEGRAM_API_TOKEN='your_token'")
        print("  export GREEN_API_ID='your_instance_id'")
        print("  export GREEN_API_TOKEN='your_api_token'")
