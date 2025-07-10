from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_start_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🤔 Как заказать?"),
                KeyboardButton(text="📋 Оформить заказ"),
            ],
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="📦 Мои заказы"),
            ],
            [
                KeyboardButton(text="📍 Адреса"),
                KeyboardButton(text="💱 Курс валют"),
            ],
            [
                KeyboardButton(text="🧮 Калькулятор"),
                KeyboardButton(text="💬 Поддержка"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие...",
    )
    return keyboard
