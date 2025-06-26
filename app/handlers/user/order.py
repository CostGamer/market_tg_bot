import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from app.repositories import AddressRepo, UserRepo, OrderRepo, AdminSettingsRepo
from app.configs import db_connection
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
from app.services import ProfileService, OrderService, CategoryHelper
from app.utils import is_valid_url

logger = logging.getLogger(__name__)
order_router = Router()


async def check_cancel(message: types.Message, state: FSMContext):
    if message.text and message.text.strip() == "Отмена":
        await message.answer(
            "Оформление заказа отменено.", reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return True
    return False


@order_router.message(Command("order"))
async def start_order(message: types.Message, state: FSMContext):
    async with db_connection.get_session() as session:
        profile_service = ProfileService(UserRepo(session))
        address_repo = AddressRepo(session)
        order_service = OrderService(OrderRepo(session), AdminSettingsRepo(session))

        user = await profile_service.get_user(message.from_user.id)  # type: ignore
        addresses = await address_repo.get_user_addresses(message.from_user.id)  # type: ignore

        ready, error_msg = await order_service.check_user_ready_for_order(
            user, bool(addresses)
        )

        if not ready:
            await message.answer(error_msg, reply_markup=ReplyKeyboardRemove())  # type: ignore
            await state.clear()
            return

        await state.update_data(
            phone=user.phone,  # type: ignore
            tg_username=user.tg_username,  # type: ignore
            addresses=[a.model_dump() for a in addresses],  # type: ignore
        )

        profile_text = (
            "👤 <b>Ваши данные для заказа:</b>\n\n"
            f"📱 <b>Телефон:</b> {user.phone}\n"  # type: ignore
        )

        if user.tg_username:  # type: ignore
            profile_text += f"👤 <b>Username:</b> @{user.tg_username}\n\n"  # type: ignore
        else:
            profile_text += "👤 <b>Username:</b> не указан\n\n"

        profile_text += (
            "Если данные неверны, отмените оформление заказа и используйте /profile для редактирования.\n\n"
            "Всё верно?"
        )

        await message.answer(
            profile_text, reply_markup=get_yes_no_keyboard(), parse_mode="HTML"
        )
        await state.set_state(OrderStates.confirm_profile)


@order_router.message(OrderStates.confirm_profile)
async def confirm_profile(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    if "да" in message.text.lower():  # type: ignore
        data = await state.get_data()
        addresses = data.get("addresses", [])

        if len(addresses) == 1:
            address = addresses[0]
            await state.update_data(address_id=address["id"], address_full=address)

            async with db_connection.get_session() as session:
                order_service = OrderService(
                    OrderRepo(session), AdminSettingsRepo(session)
                )
                address_str = order_service.format_address(address)

            await message.answer(
                f"📍 Адрес доставки:\n{address_str}\n\nВсё верно?",
                reply_markup=get_yes_no_keyboard(),
            )
            await state.set_state(OrderStates.confirm_address)
        else:
            kb = get_addresses_keyboard_order(addresses)
            await message.answer("📍 Выберите адрес доставки:", reply_markup=kb)
            await state.set_state(OrderStates.choosing_address)
    else:
        await message.answer(
            "❌ Оформление заказа отменено.\n\n"
            "Используйте команду /profile для редактирования ваших данных, "
            "затем снова отправьте /order для оформления заказа.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()


@order_router.message(OrderStates.choosing_address)
async def choose_address(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    data = await state.get_data()
    addresses = data.get("addresses", [])

    address = next((a for a in addresses if a["name"] == message.text.strip()), None)  # type: ignore

    if not address:
        await message.answer(
            "❌ Адрес не найден! Выберите из списка:",
            reply_markup=get_addresses_keyboard_order(addresses),
        )
        return

    await state.update_data(address_id=address["id"], address_full=address)

    async with db_connection.get_session() as session:
        order_service = OrderService(OrderRepo(session), AdminSettingsRepo(session))
        address_str = order_service.format_address(address)

    await message.answer(
        f"📍 Вы выбрали адрес:\n{address_str}\n\nВсё верно?",
        reply_markup=get_yes_no_keyboard(),
    )
    await state.set_state(OrderStates.confirm_address)


@order_router.message(OrderStates.confirm_address)
async def confirm_address(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    if "да" in message.text.lower():  # type: ignore
        await message.answer(
            "🔗 Отправьте ссылку на товар:", reply_markup=get_cancel_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_url)
    else:
        data = await state.get_data()
        addresses = data.get("addresses", [])
        kb = get_addresses_keyboard_order(addresses)
        await message.answer("📍 Выберите адрес доставки:", reply_markup=kb)
        await state.set_state(OrderStates.choosing_address)


@order_router.message(OrderStates.waiting_for_url, F.text)
async def get_url(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    url = message.text.strip()  # type: ignore

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
    if await check_cancel(message, state):
        return

    if "да" in message.text.lower():  # type: ignore
        await message.answer(  # type: ignore
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
    if await check_cancel(message, state):
        return

    main_cat_id = CategoryHelper.get_main_category_id_by_name(message.text.strip())  # type: ignore

    if not main_cat_id:
        await message.answer(
            "❌ Пожалуйста, выберите категорию из списка.",
            reply_markup=get_main_categories_keyboard_reply(),
        )
        return

    await state.update_data(main_cat_id=main_cat_id)

    if not CategoryHelper.has_subcategories(main_cat_id):
        await state.update_data(sub_cat_id=None)
        await message.answer(
            "📸 Пришлите скриншот товара:", reply_markup=get_cancel_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_photo)
    else:
        await message.answer(
            "📂 Выберите подкатегорию:",
            reply_markup=get_subcategories_keyboard_reply(main_cat_id),
        )
        await state.set_state(OrderStates.waiting_for_subcategory)


@order_router.message(OrderStates.waiting_for_subcategory)
async def subcategory_selected(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    data = await state.get_data()
    main_cat_id = data.get("main_cat_id")

    if message.text.strip() == "⬅️ Назад":  # type: ignore
        await message.answer(  # type: ignore
            "📂 Выберите основную категорию товара:",
            reply_markup=get_main_categories_keyboard_reply(),
        )
        await state.set_state(OrderStates.waiting_for_main_category)
        return

    subcat_id = CategoryHelper.get_subcategory_id_by_name(
        main_cat_id, message.text.strip()  # type: ignore
    )

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
    if await check_cancel(message, state):
        return

    photo = message.photo[-1]  # type: ignore
    file_id = photo.file_id

    await state.update_data(photo_url=file_id)
    await message.answer(
        "💴 Укажите цену товара (в юанях):", reply_markup=get_cancel_keyboard()
    )
    await state.set_state(OrderStates.waiting_for_price)


@order_router.message(OrderStates.waiting_for_photo)
async def photo_not_sent(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    await message.answer(
        "❌ Пожалуйста, отправьте фото товара.", reply_markup=get_cancel_keyboard()
    )


@order_router.message(OrderStates.waiting_for_price, F.text)
async def get_price(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    valid, price_yuan = CategoryHelper.validate_price(message.text)  # type: ignore

    if not valid:
        await message.answer(
            "❌ Введите корректную цену (число больше 0).",
            reply_markup=get_cancel_keyboard(),
        )
        return

    # Сохраняем цену в юанях как unit_price_yuan
    await state.update_data(unit_price_yuan=price_yuan)

    data = await state.get_data()
    main_cat_id = data.get("main_cat_id")
    sub_cat_id = data.get("sub_cat_id")

    async with db_connection.get_session() as session:
        order_service = OrderService(OrderRepo(session), AdminSettingsRepo(session))
        price_rub = await order_service.calculate_price_in_rubles(
            price_yuan, main_cat_id, sub_cat_id  # type: ignore
        )

    # Сохраняем цену в рублях как unit_price_rub
    await state.update_data(unit_price_rub=price_rub)

    await message.answer(
        f"💴 Вы указали цену: {price_yuan} юаней ({price_rub:.2f} руб).\n\nВсё верно?",
        reply_markup=get_yes_no_keyboard(),
    )
    await state.set_state(OrderStates.confirm_price)


@order_router.message(OrderStates.confirm_price)
async def confirm_price(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    if "да" in message.text.lower():  # type: ignore
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
    if await check_cancel(message, state):
        return

    text = message.text.strip()  # type: ignore

    if text in {"1", "2"}:
        quantity = int(text)
    elif text == "Другое":
        await message.answer(
            "🔢 Введите количество товара (целое число):",
            reply_markup=get_cancel_keyboard(),
        )
        return
    else:
        valid, quantity = CategoryHelper.validate_quantity(text)  # type: ignore

        if not valid:
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
    if await check_cancel(message, state):
        return

    desc = message.text.strip()  # type: ignore
    await state.update_data(description=desc)

    await message.answer(
        f"📝 Вы указали описание:\n{desc}\n\nВсё верно?",
        reply_markup=get_yes_no_keyboard(),
    )
    await state.set_state(OrderStates.confirm_description)


@order_router.message(OrderStates.confirm_description)
async def confirm_description(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    if "да" in message.text.lower():  # type: ignore
        await show_order_review(message, state)
    else:
        await message.answer(
            "📝 Опишите товар ещё раз:", reply_markup=get_cancel_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_description)


async def show_order_review(message: types.Message, state: FSMContext):
    data = await state.get_data()

    async with db_connection.get_session() as session:
        order_service = OrderService(OrderRepo(session), AdminSettingsRepo(session))
        review_text = order_service.format_order_review(data)

    photo_url = data.get("photo_url")
    if photo_url:
        await message.answer_photo(
            photo=photo_url,
            caption=review_text,
            reply_markup=get_comment_or_send_keyboard(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            review_text,
            reply_markup=get_comment_or_send_keyboard(),
            parse_mode="HTML",
        )

    await state.set_state(OrderStates.waiting_for_admin_comment)


@order_router.message(OrderStates.waiting_for_admin_comment)
async def order_admin_comment(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    text = message.text.strip()  # type: ignore

    if text == "Добавить комментарий":
        await message.answer(
            "💬 Введите комментарий для администратора:",
            reply_markup=get_cancel_keyboard(),
        )
        await state.set_state(OrderStates.waiting_for_admin_comment_text)
        return

    if text == "Отправить заказ":
        # Отправка заказа
        data = await state.get_data()

        async with db_connection.get_session() as session:
            order_service = OrderService(OrderRepo(session), AdminSettingsRepo(session))

            success, message_text = await order_service.submit_order(
                message.bot, message.from_user.id, data  # type: ignore
            )

            await message.answer(message_text, reply_markup=ReplyKeyboardRemove())

        await state.clear()
        return

    await state.update_data(admin_comment=text)
    await message.answer(
        "✅ Комментарий добавлен. Теперь нажмите 'Отправить заказ'.",
        reply_markup=get_send_order_keyboard(),
    )


@order_router.message(OrderStates.waiting_for_admin_comment_text)
async def admin_comment_text(message: types.Message, state: FSMContext):
    if await check_cancel(message, state):
        return

    comment = message.text.strip()  # type: ignore
    await state.update_data(admin_comment=comment)  # type: ignore

    await message.answer(
        "✅ Комментарий добавлен. Теперь нажмите 'Отправить заказ'.",
        reply_markup=get_send_order_keyboard(),
    )
    await state.set_state(OrderStates.waiting_for_admin_comment)
