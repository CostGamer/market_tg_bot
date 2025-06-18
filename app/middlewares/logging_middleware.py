import logging
import time

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Any, Dict, Awaitable

logger = logging.getLogger(__name__)


class LoggerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        start_time = time.time()

        user_id = None
        if hasattr(event, "from_user") and event.from_user is not None:
            user_id = event.from_user.id

        try:
            result = await handler(event, data)
            duration = f"{time.time() - start_time:.3f}s"
            logger.info(
                "Success event",
                extra={
                    "event_type": type(event).__name__,
                    "user_id": user_id,
                    "duration": duration,
                },
            )
            return result
        except Exception:
            duration = f"{time.time() - start_time:.3f}s"
            logger.error(
                "Handler error",
                exc_info=True,
                extra={
                    "event_type": type(event).__name__,
                    "user_id": user_id,
                    "duration": duration,
                },
            )
            raise
