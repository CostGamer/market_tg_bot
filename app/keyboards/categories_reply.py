from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.configs.mappers import MAIN_CATEGORY_NAMES, SUBCATEGORY_NAMES


def get_main_categories_keyboard_reply():
    keyboard = [[KeyboardButton(text=name)] for name in MAIN_CATEGORY_NAMES.values()]
    return ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
    )


def get_subcategories_keyboard_reply(main_cat_id):
    subcats = SUBCATEGORY_NAMES.get(main_cat_id, {})
    keyboard = [[KeyboardButton(text=subcat_name)] for subcat_name in subcats.values()]
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
    )
