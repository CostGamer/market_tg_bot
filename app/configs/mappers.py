KILO_MAPPER: dict = {
    "clothes": {
        "tshirt": 1,
        "jacket": 2.5,
        "jeans": 1,
        "shoes": 1.5,
        "other_clothes": 1.5,
    },
    "accessories": {
        "watch": 1,
        "bag": 1.5,
        "wallet": 1,
        "glasses": 1,
        "jewelry": 1,
        "other_accessories": 1,
    },
    "electronics": {
        "headphones": 1,
        "smartwatch": 1,
        "phone": 1,
        "laptop": 2,
        "other_electronics": 1,
    },
    "cosmetics": {"perfume": 1, "cream": 1, "lipstick": 1, "other_cosmetics": 1},
    "house": {
        "carpet": 2,
        "lamp": 1,
        "other_house": 1.5,
    },
    "toys": {
        "soft_toy": 1.5,
        "constructor": 1.5,
        "model": 1,
        "other_toys": 1.5,
    },
    "sport": {
        "tent": 3,
        "sleeping_bag": 2,
        "bicycle": 10,
        "smartwatch": 1,
        "other_sport": 2,
    },
    "other": 2,
}

MAIN_CATEGORY_NAMES = {
    "clothes": "👕👞 Одежда и обувь",
    "accessories": "👜👓 Аксессуары",
    "electronics": "💻📱 Электроника",
    "cosmetics": "💄🧴 Парфюмерия и косметика",
    "house": "🏠🛏️ Товары для дома",
    "toys": "🧸🎮 Игрушки и хобби",
    "sport": "🏕️🚴 Спорт и туризм",
    "other": "❓ Прочее",
}

SUBCATEGORY_NAMES = {
    "clothes": {
        "tshirt": "👕 Футболка, рубашка",
        "jacket": "🧥 Куртка, пуховик",
        "jeans": "👖 Джинсы, штаны",
        "shoes": "👞 Обувь",
        "other_clothes": "👚 Прочая одежда",
    },
    "accessories": {
        "watch": "⌚ Часы",
        "bag": "👜 Сумка, рюкзак",
        "wallet": "💳 Кошелек, кардхолдер",
        "glasses": "👓 Очки",
        "jewelry": "💍 Бижутерия, украшения",
        "other_accessories": "🎀 Прочее",
    },
    "electronics": {
        "headphones": "🎧 Наушники",
        "smartwatch": "⌚ Смарт-часы, браслет",
        "phone": "📱 Телефон, планшет",
        "laptop": "💻 Ноутбук",
        "other_electronics": "🔌 Прочая электроника",
    },
    "cosmetics": {
        "perfume": "🧴 Духи, туалетная вода",
        "cream": "🧴 Крем",
        "lipstick": "💄 Помада",
        "other_cosmetics": "💅 Прочая косметика",
    },
    "house": {
        "carpet": "🧶 Ковер",
        "lamp": "💡 Светильник",
        "other_house": "🏠 Прочее",
    },
    "toys": {
        "soft_toy": "🧸 Мягкие игрушки",
        "constructor": "🧩 Конструктор",
        "model": "🚗 Модельки",
        "other_toys": "🎲 Прочее",
    },
    "sport": {
        "tent": "⛺ Палатка",
        "sleeping_bag": "🛏️ Спальник",
        "bicycle": "🚲 Велосипед",
        "smartwatch": "⌚ Смарт-часы, браслет",
        "other_sport": "⚽ Прочее",
    },
}


class OrderStatus:
    NEW = "Новый"
    APPROVE_PAID = "Оплачен"
    COMING_TO_SHIPPING = "Едет на склад"
    ACCEPT_BY_SHIPPING = "На складе"
    DELIVERING = "Доставляется"
    READY_TO_GET = "Ожидает получения"
    CLOSED = "Доставлен"
    CANCELLED = "отменен"
