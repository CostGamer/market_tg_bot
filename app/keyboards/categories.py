from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_categories_keyboard() -> ReplyKeyboardMarkup:
    categories = [
        "Обувь",
        "Худи",
        "Куртка Весна",
        "Куртка Зима",
        "Футболка/Рубашка/Поло",
        "Штаны/Джинсы/Шорты",
    ]
    buttons = [[KeyboardButton(text=cat)] for cat in categories]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите категорию",
    )
