from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_yes_no_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да")], [KeyboardButton(text="❌ Нет")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_quantity_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1")],
            [KeyboardButton(text="2")],
            [KeyboardButton(text="Другое")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_send_order_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить заказ")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
