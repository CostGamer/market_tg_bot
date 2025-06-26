from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="💰 Оплачен", callback_data=f"order_status_{order_id}_paid"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇨🇳 Едет на склад",
                callback_data=f"order_status_{order_id}_shipping",
            )
        ],
        [
            InlineKeyboardButton(
                text="📦 На складе", callback_data=f"order_status_{order_id}_warehouse"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚚 Доставляется",
                callback_data=f"order_status_{order_id}_delivering",
            )
        ],
        [
            InlineKeyboardButton(
                text="📍 Ожидает получения",
                callback_data=f"order_status_{order_id}_ready",
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Доставлен", callback_data=f"order_status_{order_id}_closed"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отменить заказ",
                callback_data=f"order_status_{order_id}_cancel",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
