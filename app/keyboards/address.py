from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_addresses_keyboard(addresses):
    """Создает инлайн клавиатуру со списком адресов"""
    keyboard = []
    for address in addresses:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"📍 {address.name}", callback_data=f"address_{address.id}"
                )
            ]
        )
    keyboard.append(
        [InlineKeyboardButton(text="➕ Добавить адрес", callback_data="add_address")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_address_manage_keyboard():
    """Создает инлайн клавиатуру для управления адресом (только удаление)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить адрес", callback_data="delete_address"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к списку", callback_data="back_to_addresses"
                )
            ],
        ]
    )


def get_confirmation_keyboard():
    """Создает инлайн клавиатуру для подтверждения да/нет"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, всё верно", callback_data="confirm_yes"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Нет, ввести заново", callback_data="confirm_no"
                )
            ],
        ]
    )
