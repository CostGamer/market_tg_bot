import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from app.repositories import AddressRepo, UserRepo, OrderRepo, AdminSettingsRepo
from app.configs import db_connection, all_settings
from app.keyboards import (
    get_yes_no_keyboard,
    get_quantity_keyboard,
    get_comment_or_send_keyboard,
    get_send_order_keyboard,
    get_main_categories_keyboard_reply,
    get_subcategories_keyboard_reply,
    get_addresses_keyboard_order,
    get_cancel_keyboard,
)
from app.states import OrderStates
from app.services import ProfileService, PriceCalculator
from app.utils import is_valid_url
from app.models.pydantic_models import OrderPMPost
from app.configs.mappers import MAIN_CATEGORY_NAMES, SUBCATEGORY_NAMES, KILO_MAPPER

logger = logging.getLogger(__name__)
order_router = Router()


async def check_cancel(message: types.Message, state: FSMContext):
    """Проверка на нажатие кнопки 'Отмена'"""
    if message.text and message.text.strip() == "Отмена":
        await message.answer(
            "Оформление заказа отменено.", reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return True
    return False


@order_router.message(Command("order"))
async def start_order(message: types.Message, state: FSMContext):
    """Начало оформления заказа с проверкой профиля и адреса"""
    async with db_connection.get_session() as session:
        profile_service = ProfileService(UserRepo(session))
        address_repo = AddressRepo(session)

        # Получаем данные пользователя
        user = await profile_service.get_user(message.from_user.id)
        addresses = await address_repo.get_user_addresses(message.from_user.id)

        # Проверка профиля
        if not user or not user.phone or not user.tg_username:
            await message.answer(
                "❗️ Для оформления заказа необходимо заполнить профиль.\n\n"
                "1. Используйте команду /profile для заполнения телефона и username\n"
                "2. После этого снова отправьте /order",
                reply_markup=ReplyKeyboardRemove(),
            )
            await state.clear()
            return

        # Проверка адреса
        if not addresses:
            await message.answer(
                "❗️ Для оформления заказа необходимо добавить хотя бы один адрес доставки.\n\n"
                "1. Используйте команду /addresses для добавления адреса\n"
                "2. После этого снова отправьте /order",
                reply_markup=ReplyKeyboardRemove(),
            )
            await state.clear()
            return

        # Сохраняем данные пользователя для дальнейшего использования
        await state.update_data(
            phone=user.phone,
            tg_username=user.tg_username,
            addresses=[a.model_dump() for a in addresses],
        )

        # Показываем данные профиля для подтверждения
        profile_text = (
            "👤 **Ваши данные для заказа:**\n\n"
            f"📱 **Телефон:** {user.phone}\n"
            f"👤 **Username:** @{user.tg_username}\n\n"
            "Если данные неверны, отмените оформление заказа и используйте /profile для редактирования.\n\n"
            "Всё верно?"
        )

        await message.answer(
            profile_text, reply_markup=get_yes_no_keyboard(), parse_mode="Markdown"
        )
        await state.set_state(OrderStates.confirm_profile)


@order_router.message(OrderStates.confirm_profile)
async def confirm_profile(message: types.Message, state: FSMContext):
    """Подтверждение данных профиля"""
    if await check_cancel(message, state):
        return

    if "да" in message.text.lower():
        # Переходим к выбору адреса
        data = await state.get_data()
        addresses = data.get("addresses", [])

        if len(addresses) == 1:
            # Если адрес один, сразу подтверждаем его
            address = addresses[0]
            await state.update_data(address_id=address["id"], address_full=address)

            address_str = f"{address['city']}, {address['address']}, {address['index']}, {address['name']}"
            await message.answer(
                f"📍 Адрес доставки:\n{address_str}\n\nВсё верно?",
                reply_markup=get_yes_no_keyboard(),
            )
            await state.set_state(OrderStates.confirm_address)
        else:
            # Если адресов несколько, показываем выбор
            kb = get_addresses_keyboard_order(addresses)
            await message.answer("📍 Выберите адрес доставки:", reply_markup=kb)
            await state.set_state(OrderStates.choosing_address)
    else:
        # Отменяем оформление заказа
        await message.answer(
            "❌ Оформление заказа отменено.\n\n"
            "Используйте команду /profile для редактирования ваших данных, "
            "затем снова отправьте /order для оформления заказа.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()


@order_router.message(OrderStates.choosing_address)
async def choose_address(message: types.Message, state: FSMContext):
    """Выбор адреса доставки"""
    if await check_cancel(message, state):
        return

    data = await state.get_data()
    addresses = data.get("addresses", [])

    # Поиск выбранного адреса
    address = next((a for a in addresses if a["name"] == message.text.strip()), None)

    if not address:
        await message.answer(
            "❌ Адрес не найден! Выберите из списка:",
            reply_markup=get_addresses_keyboard_order(addresses),
        )
        return

    await state.update_data(address_id=address["id"], address_full=address)

    address_str = f"{address['city']}, {address['address']}, {address['index']}, {address['name']}"
    await message.answer(
        f"📍 Вы выбрали адрес:\n{address_str}\n\nВсё верно?",
        reply_markup=get_yes_no_keyboard(),
    )
    await state.set_state(OrderStates.confirm_address)


@order_router.message(OrderStates.confirm_address)
async def confirm_address(message: types.Message, state: FSMContext):
    """Подтверждение адреса"""
    if await check_cancel(message, state):
        return

    if "да" in message.text.lower():
        await message.answer(
            "🔗 Отправьте ссылку на товар:", reply_markup=get_cancel_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_url)
    else:
        # Возвращаемся к выбору адреса
        data = await state.get_data()
        addresses = data.get("addresses", [])
        kb = get_addresses_keyboard_order(addresses)
        await message.answer("📍 Выберите адрес доставки:", reply_markup=kb)
        await state.set_state(OrderStates.choosing_address)


@order_router.message(OrderStates.waiting_for_url, F.text)
async def get_url(message: types.Message, state: FSMContext):
    """Получение ссылки на товар"""
    if await check_cancel(message, state):
        return

    url = message.text.strip()

    if not is_valid_url(url):
        await message.answer(
            "❌ Пожалуйста, введите корректную ссылку (начинается с http/https).",
            reply_markup=get_cancel_keyboard(),
        )
        return

    await state.update_data(product_url=url)
    await message.answer(
        f"🔗 Вы указали ссылку:\n{url}\n\nВсё верно?",
        reply_markup=get_yes_no_keyboard(),
    )
    await state.set_state(OrderStates.confirm_url)


@order_router.message(OrderStates.confirm_url)
async def confirm_url(message: types.Message, state: FSMContext):
    """Подтверждение ссылки"""
    if await check_cancel(message, state):
        return

    if "да" in message.text.lower():
        await message.answer(
            "📂 Выберите основную категорию товара:",
            reply_markup=get_main_categories_keyboard_reply(),
        )
        await state.set_state(OrderStates.waiting_for_main_category)
    else:
        await message.answer(
            "🔗 Отправьте ссылку на товар ещё раз:", reply_markup=get_cancel_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_url)


@order_router.message(OrderStates.waiting_for_main_category)
async def main_category_selected(message: types.Message, state: FSMContext):
    """Выбор основной категории"""
    if await check_cancel(message, state):
        return

    # Поиск ID категории по названию
    main_cat_id = None
    for k, v in MAIN_CATEGORY_NAMES.items():
        if v == message.text.strip():
            main_cat_id = k
            break

    if not main_cat_id:
        await message.answer(
            "❌ Пожалуйста, выберите категорию из списка.",
            reply_markup=get_main_categories_keyboard_reply(),
        )
        return

    await state.update_data(main_cat_id=main_cat_id)

    # Проверяем наличие подкатегорий
    subcats = KILO_MAPPER[main_cat_id]

    if isinstance(subcats, int):
        # Нет подкатегорий, переходим к фото
        await state.update_data(sub_cat_id=None)
        await message.answer(
            "📸 Пришлите скриншот товара:", reply_markup=get_cancel_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_photo)
    else:
        # Есть подкатегории, показываем их
        await message.answer(
            "📂 Выберите подкатегорию:",
            reply_markup=get_subcategories_keyboard_reply(main_cat_id),
        )
        await state.set_state(OrderStates.waiting_for_subcategory)


@order_router.message(OrderStates.waiting_for_subcategory)
async def subcategory_selected(message: types.Message, state: FSMContext):
    """Выбор подкатегории"""
    if await check_cancel(message, state):
        return

    data = await state.get_data()
    main_cat_id = data.get("main_cat_id")

    # Обработка кнопки "Назад"
    if message.text.strip() == "⬅️ Назад":
        await message.answer(
            "📂 Выберите основную категорию товара:",
            reply_markup=get_main_categories_keyboard_reply(),
        )
        await state.set_state(OrderStates.waiting_for_main_category)
        return

    # Поиск ID подкатегории
    subcat_id = None
    subcats = SUBCATEGORY_NAMES.get(main_cat_id, {})
    for k, v in subcats.items():
        if v == message.text.strip():
            subcat_id = k
            break

    if not subcat_id:
        await message.answer(
            "❌ Пожалуйста, выберите подкатегорию из списка.",
            reply_markup=get_subcategories_keyboard_reply(main_cat_id),
        )
        return

    await state.update_data(sub_cat_id=subcat_id)
    await message.answer(
        "📸 Пришлите скриншот товара:", reply_markup=get_cancel_keyboard()
    )
    await state.set_state(OrderStates.waiting_for_photo)


@order_router.message(OrderStates.waiting_for_photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    """Получение фото товара"""
    if await check_cancel(message, state):
        return

    photo = message.photo[-1]
    file_id = photo.file_id

    await state.update_data(photo_url=file_id)
    await message.answer(
        "💴 Укажите цену товара (в юанях):", reply_markup=get_cancel_keyboard()
    )
    await state.set_state(OrderStates.waiting_for_price)


@order_router.message(OrderStates.waiting_for_photo)
async def photo_not_sent(message: types.Message, state: FSMContext):
    """Обработка случая, когда отправлено не фото"""
    if await check_cancel(message, state):
        return

    await message.answer(
        "❌ Пожалуйста, отправьте фото товара.", reply_markup=get_cancel_keyboard()
    )


@order_router.message(OrderStates.waiting_for_price, F.text)
async def get_price(message: types.Message, state: FSMContext):
    """Получение цены товара"""
    if await check_cancel(message, state):
        return

    try:
        price = float(message.text.replace(",", ".").strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Введите корректную цену (число больше 0).",
            reply_markup=get_cancel_keyboard(),
        )
        return

    await state.update_data(unit_price=price)

    # Рассчитываем цену в рублях
    data = await state.get_data()
    main_cat_id = data.get("main_cat_id")
    sub_cat_id = data.get("sub_cat_id")

    async with db_connection.get_session() as session:
        admin_settings_repo = AdminSettingsRepo(session)
        calc = PriceCalculator(price, admin_settings_repo)
        rub, _ = await calc.calculate_price(
            price, category=main_cat_id, subcategory=sub_cat_id
        )

    await state.update_data(price_rub=rub)

    await message.answer(
        f"💴 Вы указали цену: {price} юаней ({rub:.2f} руб).\n\nВсё верно?",
        reply_markup=get_yes_no_keyboard(),
    )
    await state.set_state(OrderStates.confirm_price)


@order_router.message(OrderStates.confirm_price)
async def confirm_price(message: types.Message, state: FSMContext):
    """Подтверждение цены"""
    if await check_cancel(message, state):
        return

    if "да" in message.text.lower():
        await message.answer(
            "🔢 Укажите количество товара:", reply_markup=get_quantity_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_quantity)
    else:
        await message.answer(
            "💴 Укажите цену товара ещё раз:", reply_markup=get_cancel_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_price)


@order_router.message(OrderStates.waiting_for_quantity)
async def get_quantity(message: types.Message, state: FSMContext):
    """Получение количества товара"""
    if await check_cancel(message, state):
        return

    text = message.text.strip()

    if text in {"1", "2"}:
        quantity = int(text)
    elif text == "Другое":
        await message.answer(
            "🔢 Введите количество товара (целое число):",
            reply_markup=get_cancel_keyboard(),
        )
        return
    else:
        try:
            quantity = int(text)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            await message.answer(
                "❌ Введите корректное количество (целое число больше 0).",
                reply_markup=get_quantity_keyboard(),
            )
            return

    await state.update_data(quantity=quantity)
    await message.answer(
        "📝 Опишите товар (размер, цвет и т.д.):", reply_markup=get_cancel_keyboard()
    )
    await state.set_state(OrderStates.waiting_for_description)


@order_router.message(OrderStates.waiting_for_description, F.text)
async def get_description(message: types.Message, state: FSMContext):
    """Получение описания товара"""
    if await check_cancel(message, state):
        return

    desc = message.text.strip()
    await state.update_data(description=desc)

    await message.answer(
        f"📝 Вы указали описание:\n{desc}\n\nВсё верно?",
        reply_markup=get_yes_no_keyboard(),
    )
    await state.set_state(OrderStates.confirm_description)


@order_router.message(OrderStates.confirm_description)
async def confirm_description(message: types.Message, state: FSMContext):
    """Подтверждение описания"""
    if await check_cancel(message, state):
        return

    if "да" in message.text.lower():
        await show_order_review(message, state)
    else:
        await message.answer(
            "📝 Опишите товар ещё раз:", reply_markup=get_cancel_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_description)


async def show_order_review(message: types.Message, state: FSMContext):
    """Показ итоговой информации о заказе"""
    data = await state.get_data()

    # Формируем строку с адресом
    address = data.get("address_full")
    address_str = (
        f'{address["city"]}, {address["address"]}, {address["index"]}, {address["name"]}'
        if address
        else "[не найден]"
    )

    # Формируем название категории
    category_name = MAIN_CATEGORY_NAMES.get(data.get("main_cat_id", ""), "")
    if data.get("sub_cat_id"):
        subcategory_name = SUBCATEGORY_NAMES.get(data.get("main_cat_id"), {}).get(
            data.get("sub_cat_id"), ""
        )
        category_full = f"{category_name} / {subcategory_name}"
    else:
        category_full = category_name

    # Расчет финальной стоимости
    unit_price = data.get("unit_price", 0)
    quantity = data.get("quantity", 1)
    final_price_yuan = unit_price * quantity
    final_price_rub = data.get("price_rub", 0) * quantity

    review_text = (
        "📋 **Проверьте ваш заказ:**\n\n"
        f"🔗 **Ссылка:** {data.get('product_url')}\n"
        f"📸 **Фото:** отправлено\n"
        f"📂 **Категория:** {category_full}\n"
        f"💴 **Цена:** {unit_price} юаней ({data.get('price_rub', 0):.2f} руб)\n"
        f"🔢 **Количество:** {quantity}\n"
        f"💰 **Итого:** {final_price_yuan} юаней ({final_price_rub:.2f} руб)\n"
        f"📝 **Описание:** {data.get('description')}\n"
        f"📍 **Адрес:** {address_str}\n"
        f"📱 **Телефон:** {data.get('phone')}\n"
        f"👤 **Username:** @{data.get('tg_username')}\n\n"
        "Если хотите добавить комментарий для администратора, нажмите соответствующую кнопку."
    )

    # Отправляем фото с подписью
    photo_url = data.get("photo_url")
    if photo_url:
        await message.answer_photo(
            photo=photo_url,
            caption=review_text,
            reply_markup=get_comment_or_send_keyboard(),
            parse_mode="Markdown",
        )
    else:
        # Если фото нет, отправляем только текст
        await message.answer(
            review_text,
            reply_markup=get_comment_or_send_keyboard(),
            parse_mode="Markdown",
        )

    await state.set_state(OrderStates.waiting_for_admin_comment)


@order_router.message(OrderStates.waiting_for_admin_comment)
async def order_admin_comment(message: types.Message, state: FSMContext):
    """Обработка комментария для админа"""
    if await check_cancel(message, state):
        return

    text = message.text.strip()

    if text == "Добавить комментарий":
        await message.answer(
            "💬 Введите комментарий для администратора:",
            reply_markup=get_cancel_keyboard(),
        )
        await state.set_state(OrderStates.waiting_for_admin_comment_text)
        return

    if text == "Отправить заказ":
        await submit_order(message, state)
        return

    # Если это не кнопка, считаем текст комментарием
    await state.update_data(admin_comment=text)
    await message.answer(
        "✅ Комментарий добавлен. Теперь нажмите 'Отправить заказ'.",
        reply_markup=get_send_order_keyboard(),
    )


@order_router.message(OrderStates.waiting_for_admin_comment_text)
async def admin_comment_text(message: types.Message, state: FSMContext):
    """Получение текста комментария"""
    if await check_cancel(message, state):
        return

    comment = message.text.strip()
    await state.update_data(admin_comment=comment)

    await message.answer(
        "✅ Комментарий добавлен. Теперь нажмите 'Отправить заказ'.",
        reply_markup=get_send_order_keyboard(),
    )
    await state.set_state(OrderStates.waiting_for_admin_comment)


async def submit_order(message: types.Message, state: FSMContext):
    """Отправка заказа"""
    data = await state.get_data()
    address = data.get("address_full")

    async with db_connection.get_session() as session:
        order_repo = OrderRepo(session)

        # Создаем заказ
        order_data = OrderPMPost(
            description=data["description"],
            product_url=data["product_url"],
            final_price=float(data["unit_price"]) * int(data["quantity"]),
            status="новый",
            quantity=int(data["quantity"]),
            unit_price=float(data["unit_price"]),
            photo_url=data["photo_url"],
            track_cn="",
            track_ru="",
            address_id=data["address_id"],
            user_id=message.from_user.id,
        )

        # Создаем заказ и получаем объект с ID
        created_order = await order_repo.create_order(message.from_user.id, order_data)

        if created_order:
            # Формируем сообщение для админов
            address_str = (
                f'{address["city"]}, {address["address"]}, {address["index"]}, {address["name"]}'
                if address
                else "[не найден]"
            )

            # Формируем название категории
            category_name = MAIN_CATEGORY_NAMES.get(data.get("main_cat_id", ""), "")
            if data.get("sub_cat_id"):
                subcategory_name = SUBCATEGORY_NAMES.get(
                    data.get("main_cat_id"), {}
                ).get(data.get("sub_cat_id"), "")
                category_full = f"{category_name} / {subcategory_name}"
            else:
                category_full = category_name

            admin_comment = data.get("admin_comment", "")

            # Используем user_id из created_order для номера заказа
            admin_text = (
                f"🆕 <b>Новый заказ от пользователя #{created_order.user_id}</b>\n\n"
                f"👤 <b>Пользователь:</b> @{data.get('tg_username')}\n"
                f"📱 <b>Телефон:</b> {data.get('phone')}\n\n"
                f"🔗 <b>Ссылка:</b> {created_order.product_url}\n"
                f"📂 <b>Категория:</b> {category_full}\n"
                f"💴 <b>Цена:</b> {created_order.unit_price} юаней × {created_order.quantity} = {created_order.final_price} юаней "
                f"({data.get('price_rub', 0) * data.get('quantity'):.2f} руб)\n"
                f"📝 <b>Описание:</b> {created_order.description}\n"
                f"📍 <b>Адрес:</b> {address_str}\n"
            )

            if admin_comment:
                admin_text += f"💬 <b>Комментарий:</b> {admin_comment}"

            # Отправляем сообщение в группу админов
            await message.bot.send_photo(
                chat_id=all_settings.different.orders_group_id,
                photo=created_order.photo_url,
                caption=admin_text,
                parse_mode="HTML",
            )

            await message.answer(
                "✅ Заказ успешно оформлен и отправлен на обработку!\n\n"
                "Администратор свяжется с вами в ближайшее время.",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте ещё раз.",
                reply_markup=ReplyKeyboardRemove(),
            )

    await state.clear()
