def format_order_info(order) -> str:
    username = getattr(order.user, "username", None) if hasattr(order, "user") else None
    tg_id = getattr(order.user, "tg_id", None) if hasattr(order, "user") else None
    user_display = username or tg_id or "Неизвестно"

    created_at = (
        order.created_at.strftime("%d.%m.%Y %H:%M")
        if hasattr(order, "created_at")
        else "Не указано"
    )
    status = getattr(order, "status", "Неизвестно")
    final_price = getattr(order, "final_price", 0)
    description = getattr(order, "description", "Не указано") or "Не указано"
    track_cn = getattr(order, "track_cn", None) or "Не указан"
    track_ru = getattr(order, "track_ru", None) or "Не указан"
    quantity = getattr(order, "quantity", 0)
    unit_price = getattr(order, "unit_price", 0)

    return f"""
📋 <b>Заказ #{order.id}</b>

👤 <b>Пользователь:</b> {user_display}
📅 <b>Дата создания:</b> {created_at}
📊 <b>Текущий статус:</b> {status}
💰 <b>Сумма:</b> {final_price}₽ ({quantity} × {unit_price}₽)

🛍️ <b>Товары:</b>
{description}

🇨🇳 <b>Трек Китай:</b> {track_cn}
🇷🇺 <b>Трек Россия:</b> {track_ru}

<b>Выберите действие:</b>
    """
