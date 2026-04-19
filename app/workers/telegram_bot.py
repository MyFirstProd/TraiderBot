from __future__ import annotations

import asyncio
from urllib.parse import urlencode

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.types.menu_button_web_app import MenuButtonWebApp
from aiogram.exceptions import TelegramBadRequest

from app.config.settings import get_settings
from app.core.security import create_mini_app_token
from app.db.session import SessionLocal
from app.services.config_service import ConfigService
from app.services.container import get_container
from app.utils.logging import configure_logging, get_logger

settings = get_settings()
runtime = get_container().runtime
logger = get_logger("telegram-bot")
dispatcher = Dispatcher()

BTN_STATUS = "Статус"
BTN_POSITIONS = "Позиции"
BTN_SIGNALS = "Сигналы"
BTN_RISK = "Риск"
BTN_TRADES = "Сделки"
BTN_MINIAPP = "Mini App"
BTN_ENABLE = "Включить торговлю"
BTN_DISABLE = "Отключить торговлю"


def _is_allowed(message: Message) -> bool:
    allowed = settings.TELEGRAM_ALLOWED_USERS
    if not allowed:
        return True
    return bool(message.from_user and message.from_user.id in allowed)


def _mini_app_url(user_id: int | None = None) -> str:
    base_url = settings.TELEGRAM_MINI_APP_URL or "http://localhost:8000/api/v1/telegram/miniapp"
    if not user_id:
        return base_url
    token = create_mini_app_token(user_id=user_id, ttl_seconds=settings.TELEGRAM_INITDATA_TTL_SECONDS)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode({'token': token})}"


def _mini_app_https_enabled() -> bool:
    return _mini_app_url().startswith("https://")


def _main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_POSITIONS)],
            [KeyboardButton(text=BTN_SIGNALS), KeyboardButton(text=BTN_RISK)],
            [KeyboardButton(text=BTN_TRADES), KeyboardButton(text=BTN_MINIAPP)],
            [KeyboardButton(text=BTN_ENABLE), KeyboardButton(text=BTN_DISABLE)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


def _mini_app_keyboard(user_id: int | None) -> InlineKeyboardMarkup | None:
    if not _mini_app_https_enabled():
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть Mini App",
                    web_app=WebAppInfo(url=_mini_app_url(user_id)),
                )
            ],
        ]
    )


async def _send_overview(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    await message.answer(
        "TraiderBot запущен.\n"
        "Кнопки ниже открывают статус, риск, сигналы и историю без ручного ввода команд.",
        reply_markup=_main_keyboard(),
    )
    await message.answer(
        "Mini App открывает дашборд с графиками рынка, китов, новостей, сделок, риска и обучения модели."
        + (
            ""
            if _mini_app_https_enabled()
            else f"\nСейчас активен локальный URL: {_mini_app_url(user_id)}\nДля открытия именно внутри Telegram нужен публичный HTTPS-адрес."
        ),
        reply_markup=_mini_app_keyboard(user_id),
    )


@dispatcher.message(Command("start"))
async def start_command(message: Message) -> None:
    if not _is_allowed(message):
        return
    await _send_overview(message)


@dispatcher.message(Command("miniapp"))
@dispatcher.message(F.text == BTN_MINIAPP)
async def mini_app_command(message: Message) -> None:
    if not _is_allowed(message):
        return
    user_id = message.from_user.id if message.from_user else None
    await message.answer(
        "Откройте Mini App для просмотра графиков, расчётов, торговли и обучения модели.",
        reply_markup=_mini_app_keyboard(user_id),
    )


@dispatcher.message(Command("status"))
@dispatcher.message(F.text == BTN_STATUS)
async def status_command(message: Message) -> None:
    if not _is_allowed(message):
        return
    await message.answer(
        f"Капитал: {runtime.equity:.2f}\n"
        f"Открытых позиций: {len(runtime.paper.positions)}\n"
        f"Торговля включена: {'да' if runtime.trading_enabled else 'нет'}\n"
        f"Circuit breaker: {'включен' if runtime.risk.circuit_breaker_open else 'выключен'}"
    )


@dispatcher.message(Command("enable"))
@dispatcher.message(F.text == BTN_ENABLE)
async def enable_command(message: Message) -> None:
    if not _is_allowed(message):
        return
    runtime.trading_enabled = True
    await message.answer("Paper trading включен")


@dispatcher.message(Command("disable"))
@dispatcher.message(F.text == BTN_DISABLE)
async def disable_command(message: Message) -> None:
    if not _is_allowed(message):
        return
    runtime.trading_enabled = False
    await message.answer("Paper trading отключен")


@dispatcher.message(Command("positions"))
@dispatcher.message(F.text == BTN_POSITIONS)
async def positions_command(message: Message) -> None:
    if not _is_allowed(message):
        return
    if not runtime.paper.positions:
        await message.answer("Открытых позиций нет")
        return
    lines = []
    for pos in runtime.paper.positions.values():
        side = "лонг" if pos.side == "long" else "шорт"
        lines.append(f"{pos.symbol} {side} qty={pos.quantity:.4f} entry={pos.entry_price:.4f}")
    await message.answer("\n".join(lines))


@dispatcher.message(Command("trades"))
@dispatcher.message(F.text == BTN_TRADES)
async def trades_command(message: Message) -> None:
    if not _is_allowed(message):
        return
    async with SessionLocal() as session:
        try:
            repo = ConfigService(session)
            await repo.ensure_defaults()
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    await message.answer(
        "История сделок доступна в Mini App и по API: /api/v1/market/trades",
        reply_markup=_mini_app_keyboard(message.from_user.id if message.from_user else None),
    )


@dispatcher.message(Command("risk"))
@dispatcher.message(F.text == BTN_RISK)
async def risk_command(message: Message) -> None:
    if not _is_allowed(message):
        return
    await message.answer(
        f"Дневной PnL: {runtime.risk.daily_realized_pnl:.2f}\n"
        f"Серия убытков: {runtime.risk.consecutive_losses}\n"
        f"Circuit breaker: {'включен' if runtime.risk.circuit_breaker_open else 'выключен'}\n"
        f"Макс. позиций: {runtime.risk.max_concurrent_positions}"
    )


@dispatcher.message(Command("signals"))
@dispatcher.message(F.text == BTN_SIGNALS)
async def signals_command(message: Message) -> None:
    if not _is_allowed(message):
        return
    await message.answer(
        "Сигналы доступны в Mini App и по API: /api/v1/market/signals",
        reply_markup=_mini_app_keyboard(message.from_user.id if message.from_user else None),
    )


@dispatcher.message()
async def fallback_handler(message: Message) -> None:
    if not _is_allowed(message):
        return
    await _send_overview(message)


async def run() -> None:
    token = settings.TELEGRAM_BOT_TOKEN.get_secret_value()
    if not token:
        logger.warning("telegram_bot_disabled", reason="missing_token")
        return
    bot = Bot(token=token)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Старт и клавиатура"),
            BotCommand(command="miniapp", description="Открыть дашборд"),
            BotCommand(command="status", description="Текущий статус"),
            BotCommand(command="positions", description="Открытые позиции"),
            BotCommand(command="signals", description="Последние сигналы"),
            BotCommand(command="risk", description="Риск-параметры"),
            BotCommand(command="trades", description="История сделок"),
            BotCommand(command="enable", description="Включить торговлю"),
            BotCommand(command="disable", description="Отключить торговлю"),
        ]
    )
    if _mini_app_https_enabled():
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Открыть Mini App",
                    web_app=WebAppInfo(url=_mini_app_url()),
                )
            )
        except TelegramBadRequest:
            logger.warning("telegram_menu_button_skipped", reason="invalid_webapp_url", url=_mini_app_url())
    else:
        logger.warning("telegram_menu_button_skipped", reason="https_required", url=_mini_app_url())
    logger.info("telegram_bot_starting")
    await dispatcher.start_polling(bot)


def main() -> None:
    configure_logging(settings.DEBUG)
    asyncio.run(run())


if __name__ == "__main__":
    main()
