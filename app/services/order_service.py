from typing import Dict, Any, Optional
from app.repositories import OrderRepo, AdminSettingsRepo
from app.models.pydantic_models import OrderPMPost, UserPM
from app.services import PriceCalculator
from app.configs.mappers import MAIN_CATEGORY_NAMES, SUBCATEGORY_NAMES, OrderStatus
from aiogram import Bot
from app.configs import all_settings
import html


class OrderService:
    def __init__(self, order_repo: OrderRepo, admin_settings_repo: AdminSettingsRepo):
        self.order_repo = order_repo
        self.admin_settings_repo = admin_settings_repo

    def _escape_html(self, text: str) -> str:
        if not text:
            return ""
        return html.escape(str(text))

    async def check_user_ready_for_order(
        self, user: Optional[UserPM], has_addresses: bool
    ) -> tuple[bool, Optional[str]]:
        if not user or not user.phone:
            error_msg = (
                "❗️ Для оформления заказа необходимо заполнить профиль и адрес.\n\n"
                "1. Используйте команду /profile для заполнения телефона\n"
                "2. Используйте команду /addresses для добавления адреса\n"
                "3. После этого снова отправьте /order"
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

        unit_price_yuan = data.get("unit_price_yuan", 0)
        unit_price_rub = data.get("unit_price_rub", 0)
        quantity = data.get("quantity", 1)
        final_price_yuan = unit_price_yuan * quantity
        final_price_rub = unit_price_rub * quantity

        product_url = self._escape_html(data.get("product_url", ""))
        description = self._escape_html(data.get("description", ""))
        phone = self._escape_html(data.get("phone", ""))
        tg_username = data.get("tg_username", "")
        address_str_escaped = self._escape_html(address_str)
        category_full_escaped = self._escape_html(category_full)

        username_str = (
            f"@{self._escape_html(tg_username)}" if tg_username else "не указан"
        )

        return (
            "📋 <b>Проверьте ваш заказ:</b>\n\n"
            f"🔗 <b>Ссылка:</b> {product_url}\n"
            f"📸 <b>Фото:</b> отправлено\n"
            f"📂 <b>Категория:</b> {category_full_escaped}\n"
            f"💴 <b>Цена:</b> {unit_price_yuan} юаней ({unit_price_rub:.2f} руб)\n"
            f"🔢 <b>Количество:</b> {quantity}\n"
            f"💰 <b>Итого:</b> {final_price_yuan} юаней ({final_price_rub:.2f} руб)\n"
            f"📝 <b>Описание:</b> {description}\n"
            f"📍 <b>Адрес:</b> {address_str_escaped}\n"
            f"📱 <b>Телефон:</b> {phone}\n"
            f"👤 <b>Username:</b> {username_str}\n\n"
            "Если хотите добавить комментарий для администратора, нажмите соответствующую кнопку."
        )

    def prepare_order_data(self, data: Dict[str, Any], user_id: int) -> OrderPMPost:
        unit_price_yuan = float(data["unit_price_yuan"])
        unit_price_rub = float(data["unit_price_rub"])
        quantity = int(data["quantity"])
        final_price_rub = unit_price_rub * quantity

        return OrderPMPost(  # type: ignore
            description=data["description"],
            product_url=data["product_url"],
            final_price=final_price_rub,  # Финальная цена в рублях
            status=OrderStatus.NEW,
            quantity=quantity,
            unit_price_rmb=unit_price_yuan,  # Цена за единицу в юанях
            unit_price_rub=unit_price_rub,  # Цена за единицу в рублях
            photo_url=data.get("photo_url"),
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

        tg_username = data.get("tg_username", "")
        phone = self._escape_html(data.get("phone", ""))
        product_url = self._escape_html(order.product_url)
        description = self._escape_html(order.description)
        address_str_escaped = self._escape_html(address_str)
        category_full_escaped = self._escape_html(category_full)
        admin_comment_escaped = self._escape_html(admin_comment)

        username_str = (
            f"@{self._escape_html(tg_username)}" if tg_username else "не указан"
        )

        total_yuan = order.unit_price_rmb * order.quantity

        admin_text = (
            f"🆕 <b>Новый заказ #{order.id}</b>\n\n"
            f"👤 <b>Пользователь:</b> {username_str}\n"
            f"📱 <b>Телефон:</b> {phone}\n\n"
            f"🔗 <b>Ссылка:</b> {product_url}\n"
            f"📂 <b>Категория:</b> {category_full_escaped}\n"
            f"💴 <b>Цена:</b> {order.unit_price_rmb} юаней × {order.quantity} = {total_yuan} юаней "
            f"({order.final_price:.2f} руб)\n"
            f"📝 <b>Описание:</b> {description}\n"
            f"📍 <b>Адрес:</b> {address_str_escaped}\n"
        )

        if admin_comment:
            admin_text += f"💬 <b>Комментарий:</b> {admin_comment_escaped}"

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

        if order.photo_url:
            await bot.send_photo(
                chat_id=all_settings.different.orders_group_id,
                photo=order.photo_url,
                caption=admin_text,
                parse_mode="HTML",
            )
        else:
            await bot.send_message(
                chat_id=all_settings.different.orders_group_id,
                text=admin_text,
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
