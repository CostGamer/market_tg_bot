from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.configs.mappers import KILO_MAPPER, SUBCATEGORY_NAMES, MAIN_CATEGORY_NAMES


def get_main_categories_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=MAIN_CATEGORY_NAMES[cat_id], callback_data=f"maincat_{cat_id}"
            )
        ]
        for cat_id in KILO_MAPPER.keys()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subcategories_keyboard(main_cat_id: str) -> InlineKeyboardMarkup | None:
    subcats = KILO_MAPPER[main_cat_id]
    if isinstance(subcats, int):
        return None
    buttons = [
        [
            InlineKeyboardButton(
                text=SUBCATEGORY_NAMES[main_cat_id][sub_id],
                callback_data=f"subcat_{main_cat_id}_{sub_id}",
            )
        ]
        for sub_id in subcats.keys()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
