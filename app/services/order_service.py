from typing import Dict, Any, Optional
from app.repositories import OrderRepo, AdminSettingsRepo
from app.models.pydantic_models import OrderPMPost, UserPM
from app.services import PriceCalculator
from app.configs.mappers import MAIN_CATEGORY_NAMES, SUBCATEGORY_NAMES
from aiogram import Bot
from app.configs import all_settings


class OrderService:
    def __init__(self, order_repo: OrderRepo, admin_settings_repo: AdminSettingsRepo):
        self.order_repo = order_repo
        self.admin_settings_repo = admin_settings_repo

    async def check_user_ready_for_order(
        self, user: Optional[UserPM], has_addresses: bool
    ) -> tuple[bool, Optional[str]]:
        if not user or not user.phone or not user.tg_username:
            error_msg = (
                "❗️ Для оформления заказа необходимо заполнить профиль.\n\n"
                "1. Используйте команду /profile для заполнения телефона и username\n"
                "2. После этого снова отправьте /order"
            )
            return False, error_msg

        if not has_addresses:
            error_msg = (
                "❗️ Для оформления заказа необходимо добавить хотя бы один адрес доставки.\n\n"
                "1. Используйте команду /addresses для добавления адреса\n"
                "2. После этого снова отправьте /order"
            )
            return False, error_msg

        return True, None

    def format_address(self, address: Dict[str, Any]) -> str:
        return f"{address['city']}, {address['address']}, {address['index']}, {address['name']}"

    def format_category(self, main_cat_id: str, sub_cat_id: Optional[str]) -> str:
        category_name = MAIN_CATEGORY_NAMES.get(main_cat_id, "")

        if sub_cat_id:
            subcategory_name = SUBCATEGORY_NAMES.get(main_cat_id, {}).get(
                sub_cat_id, ""
            )
            return f"{category_name} / {subcategory_name}"

        return category_name

    async def calculate_price_in_rubles(
        self, price_yuan: float, main_cat_id: str, sub_cat_id: Optional[str]
    ) -> float:
        calc = PriceCalculator(price_yuan, self.admin_settings_repo)
        rub, _ = await calc.calculate_price(
            price_yuan, category=main_cat_id, subcategory=sub_cat_id
        )
        return rub

    def format_order_review(self, data: Dict[str, Any]) -> str:
        address = data.get("address_full")
        address_str = self.format_address(address) if address else "[не найден]"
        category_full = self.format_category(
            data.get("main_cat_id", ""), data.get("sub_cat_id")
        )

        unit_price = data.get("unit_price", 0)
        quantity = data.get("quantity", 1)
        final_price_yuan = unit_price * quantity
        final_price_rub = data.get("price_rub", 0) * quantity

        return (
            "📋 **Проверьте ваш заказ:**\n\n"
            f"🔗 **Ссылка:** {data.get('product_url')}\n"
            f"📸 **Фото:** отправлено\n"
            f"📂 **Категория:** {category_full}\n"
            f"💴 **Цена:** {unit_price} юаней ({data.get('price_rub', 0):.2f} руб)\n"
            f"🔢 **Количество:** {quantity}\n"
            f"💰 **Итого:** {final_price_yuan} юаней ({final_price_rub:.2f} руб)\n"
            f"📝 **Описание:** {data.get('description')}\n"
            f"📍 **Адрес:** {address_str}\n"
            f"📱 **Телефон:** {data.get('phone')}\n"
            f"👤 **Username:** @{data.get('tg_username')}\n\n"
            "Если хотите добавить комментарий для администратора, нажмите соответствующую кнопку."
        )

    def prepare_order_data(self, data: Dict[str, Any], user_id: int) -> OrderPMPost:
        return OrderPMPost(
            description=data["description"],
            product_url=data["product_url"],
            final_price=float(data["unit_price"]) * int(data["quantity"]),
            status="новый",
            quantity=int(data["quantity"]),
            unit_price=float(data["unit_price"]),
            photo_url=data["photo_url"],
            track_cn="",
            track_ru="",
            address_id=data["address_id"],
            user_id=user_id,
        )

    def format_admin_notification(
        self, order: OrderPMPost, data: Dict[str, Any]
    ) -> str:
        address = data.get("address_full")
        address_str = self.format_address(address) if address else "[не найден]"
        category_full = self.format_category(
            data.get("main_cat_id", ""), data.get("sub_cat_id")
        )

        admin_comment = data.get("admin_comment", "")

        admin_text = (
            f"🆕 <b>Новый заказ #{order.id}</b>\n\n"
            f"👤 <b>Пользователь:</b> @{data.get('tg_username')}\n"
            f"📱 <b>Телефон:</b> {data.get('phone')}\n\n"
            f"🔗 <b>Ссылка:</b> {order.product_url}\n"
            f"📂 <b>Категория:</b> {category_full}\n"
            f"💴 <b>Цена:</b> {order.unit_price} юаней × {order.quantity} = {order.final_price} юаней "
            f"({data.get('price_rub', 0) * data.get('quantity'):.2f} руб)\n"
            f"📝 <b>Описание:</b> {order.description}\n"
            f"📍 <b>Адрес:</b> {address_str}\n"
        )

        if admin_comment:
            admin_text += f"💬 <b>Комментарий:</b> {admin_comment}"

        return admin_text

    async def create_order(
        self, user_id: int, data: Dict[str, Any]
    ) -> Optional[OrderPMPost]:
        order_data = self.prepare_order_data(data, user_id)
        return await self.order_repo.create_order(user_id, order_data)

    async def send_admin_notification(
        self, bot: Bot, order: OrderPMPost, data: Dict[str, Any]
    ) -> None:
        admin_text = self.format_admin_notification(order, data)

        await bot.send_photo(
            chat_id=all_settings.different.orders_group_id,
            photo=order.photo_url,
            caption=admin_text,
            parse_mode="HTML",
        )

    async def submit_order(
        self, bot: Bot, user_id: int, data: Dict[str, Any]
    ) -> tuple[bool, str]:
        created_order = await self.create_order(user_id, data)

        if created_order:
            await self.send_admin_notification(bot, created_order, data)

            success_message = (
                "✅ Заказ успешно оформлен и отправлен на обработку!\n\n"
                "Администратор свяжется с вами в ближайшее время."
            )
            return True, success_message
        else:
            error_message = (
                "❌ Произошла ошибка при оформлении заказа. "
                "Пожалуйста, попробуйте ещё раз."
            )
            return False, error_message
