from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_profile_keyboard(is_edit: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if not is_edit:
        buttons.append(
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data="profile_edit")]
        )
    else:
        buttons.append(
            [InlineKeyboardButton(text="💾 Сохранить", callback_data="profile_save")]
        )
        buttons.append(
            [InlineKeyboardButton(text="❌ Отмена", callback_data="profile_cancel")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
