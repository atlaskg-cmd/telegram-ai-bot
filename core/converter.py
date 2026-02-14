"""
Core business logic for currency conversion.
Used by both Telegram and WhatsApp adapters.
"""
import logging
import requests

logger = logging.getLogger(__name__)


def get_cny_rate():
    """
    Get CNY to KGS exchange rate.
    Returns rate (float) or None if failed.
    """
    try:
        # Primary: direct CNY to KGS
        url = "https://api.exchangerate-api.com/v4/latest/CNY"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            cny_to_kgs = data['rates'].get('KGS')
            if cny_to_kgs:
                logger.info(f"CNY rate fetched: 1 CNY = {cny_to_kgs:.4f} KGS")
                return cny_to_kgs
        
        # Fallback: calculate via USD
        url_usd = "https://api.exchangerate-api.com/v4/latest/USD"
        response_usd = requests.get(url_usd, timeout=10)
        if response_usd.status_code == 200:
            data_usd = response_usd.json()
            usd_to_kgs = data_usd['rates'].get('KGS')
            usd_to_cny = data_usd['rates'].get('CNY')
            if usd_to_kgs and usd_to_cny:
                calculated = usd_to_kgs / usd_to_cny
                logger.info(f"CNY rate calculated via USD: 1 CNY = {calculated:.4f} KGS")
                return calculated
        
        return None
    except Exception as e:
        logger.error(f"Error fetching CNY rate: {e}")
        return None


def convert_cny_to_kgs(amount):
    """
    Convert CNY to KGS.
    Returns dict with result or error.
    """
    try:
        amount = float(str(amount).replace(',', '.').strip())
        if amount <= 0:
            return {"error": "Сумма должна быть больше 0!"}
        
        rate = get_cny_rate()
        if not rate:
            return {"error": "Не удалось получить курс валюты. Попробуйте позже."}
        
        result = amount * rate
        return {
            "success": True,
            "amount": amount,
            "rate": rate,
            "result": result,
            "from_currency": "CNY",
            "to_currency": "KGS",
            "formatted": f"{amount:,.2f} CNY = {result:,.2f} KGS"
        }
    except ValueError:
        return {"error": "Пожалуйста, введите число (например: 100 или 150.50)"}
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return {"error": "Ошибка при конвертации. Попробуйте позже."}


def convert_kgs_to_cny(amount):
    """
    Convert KGS to CNY.
    Returns dict with result or error.
    """
    try:
        amount = float(str(amount).replace(',', '.').strip())
        if amount <= 0:
            return {"error": "Сумма должна быть больше 0!"}
        
        rate = get_cny_rate()
        if not rate:
            return {"error": "Не удалось получить курс валюты. Попробуйте позже."}
        
        result = amount / rate
        return {
            "success": True,
            "amount": amount,
            "rate": rate,
            "result": result,
            "from_currency": "KGS",
            "to_currency": "CNY",
            "formatted": f"{amount:,.2f} KGS = {result:,.2f} CNY"
        }
    except ValueError:
        return {"error": "Пожалуйста, введите число (например: 100 или 150.50)"}
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return {"error": "Ошибка при конвертации. Попробуйте позже."}


def format_conversion_result(data):
    """
    Format conversion result for display.
    Supports both Telegram HTML and WhatsApp markdown.
    """
    if "error" in data:
        return f"❌ {data['error']}"
    
    if data.get("from_currency") == "CNY":
        return (
            f"🇨🇳 *Конвертация: Юань → Сом*\n\n"
            f"💵 Сумма: *{data['amount']:,.2f} CNY*\n"
            f"📊 Курс: 1 CNY = {data['rate']:.2f} KGS\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 Результат: *{data['result']:,.2f} KGS*"
        )
    else:
        return (
            f"🇰🇬 *Конвертация: Сом → Юань*\n\n"
            f"💵 Сумма: *{data['amount']:,.2f} KGS*\n"
            f"📊 Курс: 1 CNY = {data['rate']:.2f} KGS\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 Результат: *{data['result']:,.2f} CNY*"
        )


# For compatibility with existing code
def get_currency():
    """Get USD rates (for backward compatibility)."""
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            usd_to_kgs = data['rates']['KGS']
            usd_to_rub = data['rates']['RUB']
            return f"💰 Курс USD: KGS {usd_to_kgs:.2f}, RUB {usd_to_rub:.2f}"
        else:
            return "Не удалось получить данные о валюте."
    except Exception as e:
        logger.error(f'Ошибка при получении валюты: {e}')
        return "Ошибка при подключении к API валюты."
