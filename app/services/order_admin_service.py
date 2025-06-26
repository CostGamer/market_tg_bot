from app.repositories import OrderRepo
from app.configs.mappers import OrderStatus
from app.models.pydantic_models import OrderPMUpdate
from .notification_service import NotificationService
from logging import getLogger

logger = getLogger(__name__)


class OrderAdminService:
    def __init__(self, order_repo: OrderRepo, bot):
        self.order_repo = order_repo
        self.bot = bot
        self.notification_service = NotificationService(bot)

    async def update_order_status_simple(
        self, order_id: int, action: str
    ) -> dict | None:
        action_mapping = {
            "paid": {
                "status": OrderStatus.APPROVE_PAID,
                "message": "Статус изменен на 'Оплачен'",
            },
            "warehouse": {
                "status": OrderStatus.ACCEPT_BY_SHIPPING,
                "message": "Статус изменен на 'На складе'",
            },
            "closed": {"status": OrderStatus.CLOSED, "message": "Заказ закрыт"},
            "cancel": {"status": OrderStatus.CANCELLED, "message": "Заказ отменен"},
        }

        if action not in action_mapping:
            return None

        try:
            order = await self.order_repo.get_order_with_user(order_id)
            if not order:
                return None

            new_status = action_mapping[action]["status"]
            order_update = OrderPMUpdate(status=new_status)  # type: ignore

            await self.order_repo.update_order_info(order_update, order_id)

            await self.notification_service.notify_order_status_change(
                order.user.tg_id, order_id, new_status
            )

            return action_mapping[action]

        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса заказа {order_id}: {e}")
            return None

    async def update_order_with_china_track(
        self, order_id: int, china_track: str
    ) -> bool:
        try:
            order = await self.order_repo.get_order_with_user(order_id)
            if not order:
                return False

            order_update = OrderPMUpdate(  # type: ignore
                status=OrderStatus.COMING_TO_SHIPPING, track_cn=china_track
            )

            await self.order_repo.update_order_info(order_update, order_id)

            await self.notification_service.notify_order_status_change(
                order.user.tg_id, order_id, OrderStatus.COMING_TO_SHIPPING
            )

            return True

        except Exception as e:
            logger.error(
                f"Ошибка при обновлении трек-номера Китай для заказа {order_id}: {e}"
            )
            return False

    async def update_order_with_russia_track(
        self, order_id: int, russia_track: str
    ) -> bool:
        try:
            order = await self.order_repo.get_order_with_user(order_id)
            if not order:
                return False

            order_update = OrderPMUpdate(  # type: ignore
                status=OrderStatus.DELIVERING, track_ru=russia_track
            )

            await self.order_repo.update_order_info(order_update, order_id)

            await self.notification_service.notify_order_status_change_with_track(
                order.user.tg_id, order_id, OrderStatus.DELIVERING, russia_track
            )

            return True

        except Exception as e:
            logger.error(
                f"Ошибка при обновлении трек-номера Россия для заказа {order_id}: {e}"
            )
            return False

    async def update_order_to_ready_with_qr(
        self, order_id: int, qr_photo_id: str
    ) -> bool:
        try:
            order = await self.order_repo.get_order_with_user(order_id)
            if not order:
                return False

            order_update = OrderPMUpdate(status=OrderStatus.READY_TO_GET)  # type: ignore

            await self.order_repo.update_order_info(order_update, order_id)

            await self.notification_service.notify_order_ready_with_qr(
                order.user.tg_id, order_id, qr_photo_id
            )

            return True

        except Exception as e:
            logger.error(
                f"Ошибка при обновлении заказа {order_id} до готового с QR: {e}"
            )
            return False
