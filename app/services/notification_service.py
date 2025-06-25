from logging import getLogger

logger = getLogger(__name__)


class NotificationService:
    def __init__(self, bot):
        self.bot = bot

    async def notify_order_status_change(
        self, user_tg_id: int, order_id: int, new_status: str
    ):
        try:
            status_messages = {
                "Оплачен": "✅ Ваш заказ оплачен и принят в обработку",
                "Едет на склад": "📦 Ваш заказ отправлен на склад в Китае",
                "На складе": "🏭 Ваш заказ поступил на склад в Китае",
                "Доставляется": "🚚 Ваш заказ отправлен в Россию",
                "Ожидает получения": "📍 Ваш заказ прибыл и ожидает получения",
                "Доставлен": "✅ Заказ успешно доставлен",
                "Отменен": "❌ Заказ отменен",
            }

            message = f"🔔 <b>Статус заказа #{order_id} изменен</b>\n\n"
            message += status_messages.get(new_status, f"Новый статус: {new_status}")

            await self.bot.send_message(
                chat_id=user_tg_id, text=message, parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю {user_tg_id}: {e}")

    async def notify_order_status_change_with_track(
        self, user_tg_id: int, order_id: int, new_status: str, track_number: str
    ):
        try:
            status_messages = {
                "Доставляется": "🚚 Ваш заказ отправлен в Россию",
            }

            message = f"🔔 <b>Статус заказа #{order_id} изменен</b>\n\n"
            message += status_messages.get(new_status, f"Новый статус: {new_status}")
            message += f"\n\n🇷🇺 <b>Трек-номер для отслеживания:</b> <code>{track_number}</code>"
            message += "\n\n💡 <i>Скопируйте трек-номер и отследите доставку на сайте почтовой службы</i>"

            await self.bot.send_message(
                chat_id=user_tg_id, text=message, parse_mode="HTML"
            )
        except Exception as e:
            logger.error(
                f"Ошибка отправки уведомления с трек-номером пользователю {user_tg_id}: {e}"
            )

    async def notify_order_ready_with_qr(
        self, user_tg_id: int, order_id: int, qr_photo_id: str
    ):
        try:
            message = (
                f"🔔 <b>Статус заказа #{order_id} изменен</b>\n\n"
                "📍 Ваш заказ прибыл и ожидает получения\n\n"
                "📱 <b>QR-код для получения заказа:</b>\n"
                "Покажите этот QR-код при получении заказа"
            )

            await self.bot.send_photo(
                chat_id=user_tg_id,
                photo=qr_photo_id,
                caption=message,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(
                f"Ошибка отправки уведомления с QR-кодом пользователю {user_tg_id}: {e}"
            )
