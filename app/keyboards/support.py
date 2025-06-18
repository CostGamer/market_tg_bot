from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_support_faq_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, нашёл ответ")],
            [KeyboardButton(text="❌ Нет, хочу написать в поддержку")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
