from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_addresses_keyboard(addresses):
    keyboard = []
    if addresses:
        for addr in addresses:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=addr.name, callback_data=f"address_{addr.id}"
                    )
                ]
            )
    keyboard.insert(
        0, [InlineKeyboardButton(text="➕ Добавить адрес", callback_data="add_address")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_address_manage_keyboard(address_id) -> InlineKeyboardMarkup:
    # Принудительно преобразуем в строку
    address_id = str(address_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить", callback_data=f"edit_address_{address_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить", callback_data=f"delete_address_{address_id}"
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="profile_addresses")],
        ]
    )


def get_edit_address_field_keyboard(address_id):
    # Принудительно преобразуем в строку
    address_id = str(address_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Имя", callback_data=f"edit_field_name_{address_id}"
                ),
                InlineKeyboardButton(
                    text="🏙️ Город", callback_data=f"edit_field_city_{address_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Адрес", callback_data=f"edit_field_address_{address_id}"
                ),
                InlineKeyboardButton(
                    text="🔢 Индекс", callback_data=f"edit_field_index_{address_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад", callback_data=f"address_{address_id}"
                )
            ],
        ]
    )
