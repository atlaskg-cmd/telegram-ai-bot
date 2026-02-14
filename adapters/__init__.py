"""Platform adapters package."""

# Basic adapters
from .telegram_bot import run_telegram_bot
from .whatsapp_bot import run_whatsapp_bot

# Full-featured adapters (when available)
try:
    from .telegram_full import run_full_telegram_bot
    from .whatsapp_full import run_full_whatsapp_bot
    FULL_ADAPTERS_AVAILABLE = True
except ImportError:
    FULL_ADAPTERS_AVAILABLE = False

__all__ = [
    'run_telegram_bot',
    'run_whatsapp_bot',
    'run_full_telegram_bot',
    'run_full_whatsapp_bot',
    'FULL_ADAPTERS_AVAILABLE'
]
