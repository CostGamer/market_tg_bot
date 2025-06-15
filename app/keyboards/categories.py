from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

CATEGORIES = [
    "Обувь",
    "Худи",
    "Куртка Весна",
    "Куртка Зима",
    "Футболка/Рубашка/Поло",
    "Штаны/Джинсы/Шорты",
    "Аксессуары",
    "Головные уборы",
    "Платья",
    "Юбки",
    "Костюмы",
    "Спортивная одежда",
]

ITEMS_PER_PAGE = 6


def get_categories_inline_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_categories = CATEGORIES[start:end]

    keyboard = []
    row = []
    for idx, cat in enumerate(page_categories, 1):
        row.append(InlineKeyboardButton(text=cat, callback_data=f"cat_{cat}"))
        if idx % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="←", callback_data=f"cat_page_{page-1}")
        )
    if end < len(CATEGORIES):
        nav_buttons.append(
            InlineKeyboardButton(text="→", callback_data=f"cat_page_{page+1}")
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
