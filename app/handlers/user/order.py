from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from app.repositories import AddressRepo, UserRepo, OrderRepo
from app.configs import db_connection, all_settings
from app.keyboards import (
    get_yes_no_keyboard,
    get_quantity_keyboard,
    get_send_order_keyboard,
    get_addresses_keyboard,
)
from app.states import OrderStates
from app.services import ProfileService
from app.utils import is_valid_phone
from app.models.pydantic_models import AddressPM, OrderPMPost

order_router = Router()


@order_router.message(Command("order"))
async def start_order(message: types.Message, state: FSMContext):
    await message.answer("Отправьте ссылку на товар:")
    await state.set_state(OrderStates.waiting_for_url)


@order_router.message(OrderStates.waiting_for_url, F.text)
async def get_url(message: types.Message, state: FSMContext):
    url = message.text.strip()
    await state.update_data(product_url=url)
    await message.answer(
        f"Вы указали ссылку:\n{url}\n\nВсё верно?", reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(OrderStates.confirm_url)


@order_router.message(OrderStates.confirm_url)
async def confirm_url(message: types.Message, state: FSMContext):
    if "да" in message.text.lower():
        await message.answer(
            "Пришлите скриншот товара:", reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(OrderStates.waiting_for_photo)
    else:
        await message.answer(
            "Отправьте ссылку на товар ещё раз:", reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(OrderStates.waiting_for_url)


@order_router.message(OrderStates.waiting_for_photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(photo_url=file_id)
    await message.answer("Укажите цену товара (в юанях):")
    await state.set_state(OrderStates.waiting_for_price)


@order_router.message(OrderStates.waiting_for_price, F.text)
async def get_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", ".").strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную цену (число, больше 0).")
        return
    await state.update_data(unit_price=price)
    await message.answer(
        f"Вы указали цену: {price} юаней. Всё верно?",
        reply_markup=get_yes_no_keyboard(),
    )
    await state.set_state(OrderStates.confirm_price)


@order_router.message(OrderStates.confirm_price)
async def confirm_price(message: types.Message, state: FSMContext):
    if "да" in message.text.lower():
        await message.answer(
            "Укажите количество товара:", reply_markup=get_quantity_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_quantity)
    else:
        await message.answer(
            "Укажите цену товара ещё раз:", reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(OrderStates.waiting_for_price)


@order_router.message(OrderStates.waiting_for_quantity)
async def get_quantity(message: types.Message, state: FSMContext):
    if message.text.strip() in {"1", "2"}:
        quantity = int(message.text.strip())
    else:
        try:
            quantity = int(message.text.strip())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            await message.answer("Введите корректное количество (целое число).")
            return
    await state.update_data(quantity=quantity)
    await message.answer(
        "Опишите товар (размер, цвет и т.д.):", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(OrderStates.waiting_for_description)


@order_router.message(OrderStates.waiting_for_description, F.text)
async def get_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    await state.update_data(description=desc)
    await message.answer(
        f"Вы указали описание:\n{desc}\n\nВсё верно?",
        reply_markup=get_yes_no_keyboard(),
    )
    await state.set_state(OrderStates.confirm_description)


@order_router.message(OrderStates.confirm_description)
async def confirm_description(message: types.Message, state: FSMContext):
    if "да" in message.text.lower():
        async with db_connection.get_session() as session:
            address_repo = AddressRepo(session)
            addresses = await address_repo.get_user_addresses(message.from_user.id)
            if addresses:
                kb = get_addresses_keyboard(addresses)
                await message.answer("Выберите адрес доставки:", reply_markup=kb)
                await state.set_state(OrderStates.choosing_address)
            else:
                await message.answer(
                    "У вас нет сохранённых адресов. Давайте добавим новый.\n🏙️ Введите город пункта выдачи:",
                    reply_markup=ReplyKeyboardRemove(),
                )
                await state.set_state(OrderStates.waiting_for_address_city)
    else:
        await message.answer(
            "Опишите товар ещё раз:", reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(OrderStates.waiting_for_description)


@order_router.message(OrderStates.choosing_address)
async def choose_address(message: types.Message, state: FSMContext):
    text = message.text.strip()
    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)
        addresses = await address_repo.get_user_addresses(message.from_user.id)
        address = next((a for a in addresses if a.name == text), None)
        if address:
            await state.update_data(address_id=address.id)
            await ask_phone_and_username(message, state)
        else:
            await message.answer(
                "❌ Адрес не найден! Выберите из списка или добавьте новый."
            )


# Добавление нового адреса по шагам (аналогично AddressStates)
@order_router.message(OrderStates.waiting_for_address_city)
async def order_address_city(message: types.Message, state: FSMContext):
    city = message.text.strip()
    if not city:
        await message.answer("❌ Город не может быть пустым!")
        return
    await state.update_data(address_city=city)
    await message.answer("🏠 Введите адрес пункта выдачи (улица, дом, офис):")
    await state.set_state(OrderStates.waiting_for_address_address)


@order_router.message(OrderStates.waiting_for_address_address)
async def order_address_address(message: types.Message, state: FSMContext):
    address = message.text.strip()
    if not address:
        await message.answer("❌ Адрес не может быть пустым!")
        return
    await state.update_data(address_address=address)
    await message.answer("🏷️ Введите индекс пункта выдачи:")
    await state.set_state(OrderStates.waiting_for_address_index)


@order_router.message(OrderStates.waiting_for_address_index)
async def order_address_index(message: types.Message, state: FSMContext):
    index = message.text.strip()
    if not index.isdigit():
        await message.answer("❌ Индекс должен быть числом!")
        return
    await state.update_data(address_index=int(index))
    await message.answer(
        "🏷️ Введите название пункта выдачи (например, 'Boxberry Центральный'):"
    )
    await state.set_state(OrderStates.waiting_for_address_name)


@order_router.message(OrderStates.waiting_for_address_name)
async def order_address_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("❌ Название не может быть пустым!")
        return
    data = await state.get_data()
    address_data = AddressPM(
        address=data["address_address"],
        city=data["address_city"],
        index=data["address_index"],
        name=name,
    )
    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)
        new_address = await address_repo.create_address(
            message.from_user.id, address_data
        )
        if new_address:
            await state.update_data(address_id=new_address.id)
            await ask_phone_and_username(message, state)
        else:
            await message.answer("❌ Ошибка при сохранении адреса!")
            await state.clear()


# --- PHONE & USERNAME ---


async def ask_phone_and_username(message: types.Message, state: FSMContext):
    async with db_connection.get_session() as session:
        profile_service = ProfileService(UserRepo(session))
        user = await profile_service.get_user(message.from_user.id)
        if not user or not user.phone:
            await message.answer("📱 Введите ваш телефон:")
            await state.set_state(OrderStates.waiting_for_phone)
            return
        if not user.tg_username:
            await message.answer("👤 Введите ваш username (например, @username):")
            await state.set_state(OrderStates.waiting_for_username)
            return
    await show_order_review(message, state)


@order_router.message(OrderStates.waiting_for_phone)
async def order_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not is_valid_phone(phone):
        await message.answer("❌ Некорректный телефон. Пример: +79001234567")
        return
    await state.update_data(phone=phone)
    await show_order_review(message, state)


@order_router.message(OrderStates.waiting_for_username)
async def order_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    if not username.startswith("@") or len(username) < 3:
        await message.answer(
            "Пожалуйста, введите корректный username (например, @username)."
        )
        return
    await state.update_data(tg_username=username)
    await show_order_review(message, state)


# --- REVIEW & SUBMIT ---


async def show_order_review(message: types.Message, state: FSMContext):
    data = await state.get_data()
    review_text = (
        f"Проверьте ваш заказ:\n\n"
        f"Ссылка: {data.get('product_url')}\n"
        f"Фото: [отправлено]\n"
        f"Цена: {data.get('unit_price')} юаней\n"
        f"Количество: {data.get('quantity')}\n"
        f"Описание: {data.get('description')}\n"
        f"Адрес: {data.get('address_id')}\n"
        f"Телефон: {data.get('phone', '[из профиля]')}\n"
        f"Username: {data.get('tg_username', '[из профиля]')}\n\n"
        f"Если хотите, добавьте комментарий для админа или нажмите 'Отправить заказ'"
    )
    await message.answer(review_text, reply_markup=get_send_order_keyboard())
    await state.set_state(OrderStates.waiting_for_admin_comment)


@order_router.message(OrderStates.waiting_for_admin_comment)
async def order_admin_comment(message: types.Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    admin_comment = ""
    if text != "Отправить заказ":
        admin_comment = text

    async with db_connection.get_session() as session:
        order_repo = OrderRepo(session)
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
        order = await order_repo.create_order(message.from_user.id, order_data)
        if order:
            admin_text = (
                f"🆕 Новый заказ #{order.quantity} шт.\n"
                f"ID заказа: {order.user_id}\n"
                f"Ссылка: {order.product_url}\n"
                f"Цена: {order.unit_price} × {order.quantity} = {order.final_price} юаней\n"
                f"Описание: {order.description}\n"
                f"Комментарий для админа: {admin_comment or '[нет]'}"
            )
            await message.bot.send_photo(
                chat_id=all_settings.different.orders_group_id,
                photo=order.photo_url,
                caption=admin_text,
                parse_mode="HTML",
            )
            await message.answer(
                "✅ Заказ оформлен и отправлен на подтверждение!",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await message.answer(
                "❌ Ошибка при оформлении заказа. Попробуйте ещё раз.",
                reply_markup=ReplyKeyboardRemove(),
            )
    await state.clear()
