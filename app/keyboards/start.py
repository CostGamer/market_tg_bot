from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_start_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="📋 Оформить заказ"),
            ],
            [KeyboardButton(text="📍 Адреса"), KeyboardButton(text="📦 Мои заказы")],
            [
                KeyboardButton(text="💱 Курс валют"),
                KeyboardButton(text="🧮 Калькулятор"),
            ],
            [KeyboardButton(text="💬 Поддержка")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие...",
    )
    return keyboard
