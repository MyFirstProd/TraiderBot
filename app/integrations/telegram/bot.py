from __future__ import annotations

from aiogram import Bot

from app.config.settings import get_settings


class TelegramBotClient:
    def __init__(self) -> None:
        token = get_settings().TELEGRAM_BOT_TOKEN.get_secret_value()
        self.enabled = bool(token)
        self.bot = Bot(token=token) if token else None

    async def send_message(self, chat_id: int, text: str) -> None:
        if self.bot is None:
            return
        await self.bot.send_message(chat_id=chat_id, text=text)
