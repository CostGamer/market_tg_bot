from aiogram import types
from app.repositories import OrderRepo
from app.models.pydantic_models import OrderPMGet
from logging import getLogger

logger = getLogger(__name__)


class OrderHistoryService:
    def __init__(self, order_repo: OrderRepo):
        self.order_repo = order_repo

    def _escape_html(self, text: str) -> str:
        if not text:
            return ""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _get_status_emoji(self, status: str) -> str:
        status_emojis = {
            "Новый": "🆕",
            "Оплачен": "✅",
            "Едет на склад": "📦",
            "На складе": "🏭",
            "Доставляется": "🚚",
            "Ожидает получения": "📍",
            "Доставлен": "✅",
            "Отменен": "❌",
            "Закрыт": "🔒",
        }
        return status_emojis.get(status, "📄")

    def _format_order_text(self, order: OrderPMGet, order_number: int) -> str:
        description = self._escape_html(order.description)
        status = self._escape_html(order.status)
        status_emoji = self._get_status_emoji(order.status)

        text = (
            f"🆔 <b>Заказ #{order_number}</b>\n\n"
            f"📝 <b>Описание:</b> {description}\n"
            f"🔢 <b>Количество:</b> {order.quantity} шт.\n"
            f"💴 <b>Цена за единицу:</b> {order.unit_price_rmb} юаней ({order.unit_price_rub:.2f} руб.)\n"
            f"💰 <b>Итого:</b> {order.final_price:.2f} руб.\n"
            f"{status_emoji} <b>Статус:</b> {status}"
        )

        return text

    async def send_order_card(
        self, message: types.Message, order: OrderPMGet, order_number: int
    ):
        try:
            order_text = self._format_order_text(order, order_number)

            if order.photo_url:
                try:
                    await message.answer_photo(
                        photo=order.photo_url, caption=order_text, parse_mode="HTML"
                    )
                except Exception as e:
                    logger.warning(
                        f"Не удалось отправить фото для заказа {order.id}: {e}"
                    )
                    await message.answer(order_text, parse_mode="HTML")
            else:
                await message.answer(order_text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Ошибка при отправке карточки заказа: {e}")
            await message.answer(
                f"🆔 <b>Заказ #{order_number}</b>\n"
                f"💰 <b>Сумма:</b> {order.final_price:.2f} руб.\n"
                f"📄 <b>Статус:</b> {self._escape_html(order.status)}",
                parse_mode="HTML",
            )
