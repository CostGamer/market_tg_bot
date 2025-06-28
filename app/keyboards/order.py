from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Отмена", callback_data="cancel_order")]
        ]
    )


def get_yes_no_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, всё верно", callback_data="confirm_yes"
                ),
                InlineKeyboardButton(
                    text="❌ Нет, изменить", callback_data="confirm_no"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Отменить заказ", callback_data="cancel_order"
                )
            ],
        ]
    )


def get_quantity_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1️⃣ Одна штука", callback_data="quantity_1"),
                InlineKeyboardButton(text="2️⃣ Две штуки", callback_data="quantity_2"),
            ],
            [
                InlineKeyboardButton(
                    text="🔢 Ввести другое количество", callback_data="quantity_other"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Отменить заказ", callback_data="cancel_order"
                )
            ],
        ]
    )


def get_comment_or_send_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Добавить комментарий для администратора",
                    callback_data="add_comment",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 Отправить заказ", callback_data="send_order"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Отменить заказ", callback_data="cancel_order"
                )
            ],
        ]
    )


def get_send_order_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Отправить заказ", callback_data="send_order"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Отменить заказ", callback_data="cancel_order"
                )
            ],
        ]
    )


def get_addresses_keyboard_order(addresses):
    keyboard = []
    for addr in addresses:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"📍 {addr['name']}",
                    callback_data=f"address_order_{addr['id']}",
                )
            ]
        )
    keyboard.append(
        [InlineKeyboardButton(text="🚫 Отменить заказ", callback_data="cancel_order")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
