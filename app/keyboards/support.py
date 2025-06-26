from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_support_faq_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, нашёл ответ", callback_data="faq_found"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Нет, хочу написать в поддержку",
                    callback_data="faq_not_found",
                )
            ],
        ]
    )
