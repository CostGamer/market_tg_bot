import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.configs import settings

from app.handlers.user import user_router
from app.middlewares import LoggerMiddleware
from app.configs.logging_config import init_logger


def setup_handlers(dp: Dispatcher):
    dp.include_router(user_router)
    # dp.include_router(admin.router)


def setup_middlewares(dp: Dispatcher):
    dp.update.outer_middleware(LoggerMiddleware())


async def main():
    init_logger(settings.logging)
    logger = logging.getLogger(__name__)
    logger.info("Запуск Telegram-бота...")

    bot = Bot(
        token=settings.tg.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    setup_middlewares(dp)
    setup_handlers(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
