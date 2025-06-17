import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.configs import all_settings

from app.handlers.user import user_router
from app.handlers.admin import admin_router
from app.middlewares import LoggerMiddleware
from app.configs.logging_config import init_logger


def setup_handlers(dp: Dispatcher):
    dp.include_router(user_router)
    dp.include_router(admin_router)


def setup_middlewares(dp: Dispatcher):
    dp.update.outer_middleware(LoggerMiddleware())


async def main():
    init_logger(all_settings.logging)
    logger = logging.getLogger(__name__)
    logger.info("Запуск Telegram-бота...")

    bot = Bot(
        token=all_settings.tg.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    setup_middlewares(dp)
    setup_handlers(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
