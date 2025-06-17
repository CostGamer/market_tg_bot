from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data="profile_edit"
                )
            ],
        ]
    )


def get_edit_profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Имя", callback_data="edit_name"),
                InlineKeyboardButton(text="📱 Телефон", callback_data="edit_phone"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")],
        ]
    )
