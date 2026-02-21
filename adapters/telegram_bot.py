"""
Telegram Bot Adapter using aiogram.
Refactored to use core.converter for business logic.
"""
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import asyncio

from core.converter import (
    convert_cny_to_kgs, 
    convert_kgs_to_cny, 
    format_conversion_result,
    get_currency
)

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot wrapper using aiogram."""
    
    def __init__(self):
        self.api_token = os.environ.get("TELEGRAM_API_TOKEN")
        if not self.api_token:
            logger.warning("TELEGRAM_API_TOKEN not set! Telegram bot will not work.")
            self.enabled = False
            return
        
        self.bot = Bot(token=self.api_token)
        self.dp = Dispatcher()
        self.enabled = True
        
        # User states
        self.user_states = {}
        
        # Setup handlers
        self._setup_handlers()
        
        logger.info("Telegram bot initialized")
    
    def _setup_handlers(self):
        """Register message handlers."""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            await message.reply(
                "🤖 Привет! Я бот-конвертер валют.\n\n"
                "Выберите действие в меню ниже:",
                reply_markup=self.get_main_keyboard()
            )
        
        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            help_text = (
                "📖 *Справка*\n\n"
                "*Команды:*\n"
                "🇨🇳 Юань → Сом - конвертировать CNY в KGS\n"
                "🇰🇬 Сом → Юань - конвертировать KGS в CNY\n"
                "💰 Курс валют - текущий курс USD\n\n"
                "Просто нажмите кнопку и введите сумму!"
            )
            await message.reply(help_text, parse_mode="Markdown")
        
        @self.dp.message(Command("currency"))
        async def cmd_currency(message: Message):
            await message.reply(get_currency())
        
        @self.dp.message(lambda msg: msg.text == "🇨🇳 Юань → Сом")
        async def btn_cny_to_kgs(message: Message):
            user_id = message.from_user.id
            self.user_states[user_id] = "awaiting_cny_amount"
            
            await message.reply(
                "🇨🇳 *Юань → Сом*\n\n"
                "Введите сумму в юанях (CNY):",
                parse_mode="Markdown"
            )
        
        @self.dp.message(lambda msg: msg.text == "🇰🇬 Сом → Юань")
        async def btn_kgs_to_cny(message: Message):
            user_id = message.from_user.id
            self.user_states[user_id] = "awaiting_kgs_amount"
            
            await message.reply(
                "🇰🇬 *Сом → Юань*\n\n"
                "Введите сумму в сомах (KGS):",
                parse_mode="Markdown"
            )
        
        @self.dp.message(lambda msg: msg.text == "💰 Курс валют")
        async def btn_currency(message: Message):
            await message.reply(get_currency())
        
        @self.dp.message()
        async def handle_text(message: Message):
            user_id = message.from_user.id
            text = message.text.strip()
            
            # Check user state
            if user_id in self.user_states:
                state = self.user_states[user_id]
                del self.user_states[user_id]  # Clear state
                
                if state == "awaiting_cny_amount":
                    result = convert_cny_to_kgs(text)
                    await message.reply(
                        format_conversion_result(result),
                        parse_mode="Markdown",
                        reply_markup=self.get_main_keyboard()
                    )
                    return
                
                elif state == "awaiting_kgs_amount":
                    result = convert_kgs_to_cny(text)
                    await message.reply(
                        format_conversion_result(result),
                        parse_mode="Markdown",
                        reply_markup=self.get_main_keyboard()
                    )
                    return
            
            # Default: unknown command
            await message.reply(
                "❓ Не понял команду.\n"
                "Используйте меню или команду /help",
                reply_markup=self.get_main_keyboard()
            )
    
    def get_main_keyboard(self):
        """Return main reply keyboard."""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🇨🇳 Юань → Сом"), KeyboardButton(text="🇰🇬 Сом → Юань")],
                [KeyboardButton(text="💰 Курс валют"), KeyboardButton(text="❓ Помощь")]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    async def run(self):
        """Start Telegram bot polling."""
        if not self.enabled:
            logger.warning("Telegram bot is disabled (no token)")
            return
        
        logger.info("Telegram bot started!")
        await self.dp.start_polling(self.bot)


async def run_telegram_bot():
    """Entry point for running Telegram bot."""
    bot = TelegramBot()
    if bot.enabled:
        await bot.run()
    else:
        logger.warning("Telegram bot not started - token missing")
