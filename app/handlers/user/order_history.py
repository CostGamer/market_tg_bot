from aiogram import Router, types
from aiogram.filters import Command
from app.repositories import OrderRepo
from app.configs import db_connection
from app.services import OrderHistoryService
from logging import getLogger

logger = getLogger(__name__)

user_orders_router = Router()


@user_orders_router.message(Command("my_orders"))
async def show_user_orders(message: types.Message):
    try:
        async with db_connection.get_session() as session:
            order_repo = OrderRepo(session)
            order_service = OrderHistoryService(order_repo)

            orders = await order_repo.get_user_orders(message.from_user.id)  # type: ignore

            if not orders:
                await message.answer(
                    "📦 У вас пока нет заказов.\n\n"
                    "Используйте команду /order для создания первого заказа 🛒!",
                    parse_mode="HTML",
                )
                return

            await message.answer(
                f"📋 <b>Ваши заказы ({len(orders)} шт.):</b>", parse_mode="HTML"
            )

            for i, order in enumerate(orders, 1):
                await order_service.send_order_card(message, order, i)

    except Exception as e:
        logger.error(
            f"Ошибка при получении заказов пользователя {message.from_user.id}: {e}"  # type: ignore
        )
        await message.answer(
            "❌ Произошла ошибка при загрузке заказов. Попробуйте позже.",
            parse_mode="HTML",
        )
