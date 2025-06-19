from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_addresses_keyboard(addresses):
    keyboard = []
    if addresses:
        for addr in addresses:
            keyboard.append([KeyboardButton(text=addr.name)])
    keyboard.insert(0, [KeyboardButton(text="➕ Добавить адрес")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
    )


def get_address_manage_keyboard():
    keyboard = [
        [KeyboardButton(text="✏️ Изменить"), KeyboardButton(text="🗑️ Удалить")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
    )


def get_edit_address_field_keyboard():
    keyboard = [
        [KeyboardButton(text="✏️ Имя"), KeyboardButton(text="🏙️ Город")],
        [KeyboardButton(text="🏠 Адрес"), KeyboardButton(text="🔢 Индекс")],
        [KeyboardButton(text="❌ Отмена")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
    )
