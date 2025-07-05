import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.repositories import AddressRepo, UserRepo, OrderRepo, AdminSettingsRepo
from app.configs import db_connection
from app.keyboards import (
    get_cancel_keyboard,
    get_yes_no_keyboard,
    get_quantity_keyboard,
    get_comment_or_send_keyboard,
    get_send_order_keyboard,
    get_addresses_keyboard_order,
    get_main_categories_keyboard_order,
    get_subcategories_keyboard_order,
)
from app.states import OrderStates
from app.services import ProfileService, OrderService, CategoryHelper
from app.utils import is_valid_url

logger = logging.getLogger(__name__)
order_router = Router()


async def handle_cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    try:
        await callback.message.edit_text(  # type: ignore
            "🚫 Оформление заказа отменено.", reply_markup=None
        )
    except Exception:
        await callback.bot.send_message(  # type: ignore
            chat_id=callback.from_user.id, text="🚫 Оформление заказа отменено."
        )

    await state.clear()


@order_router.callback_query(F.data == "cancel_order")
async def cancel_order_callback(callback: types.CallbackQuery, state: FSMContext):
    await handle_cancel_order(callback, state)


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
            await message.answer(error_msg)  # type: ignore
            await state.clear()
            return

        await state.update_data(
            phone=user.phone,  # type: ignore
            tg_username=user.tg_username,  # type: ignore
            addresses=[a.model_dump() for a in addresses],  # type: ignore
        )

        profile_text = (
            "🛒 <b>Оформление нового заказа</b>\n\n"
            "👤 <b>Ваши данные для заказа:</b>\n\n"
            f"📱 <b>Телефон:</b> {user.phone}\n"  # type: ignore
        )

        if user.tg_username:  # type: ignore
            profile_text += f"👤 <b>Username:</b> @{user.tg_username}\n\n"  # type: ignore
        else:
            profile_text += "👤 <b>Username:</b> не указан\n\n"

        profile_text += (
            "ℹ️ Если данные неверны, отмените оформление заказа и используйте /profile для редактирования.\n\n"
            "Данные корректны?"
        )

        await message.answer(
            profile_text, reply_markup=get_yes_no_keyboard(), parse_mode="HTML"
        )
        await state.set_state(OrderStates.confirm_profile)


@order_router.callback_query(OrderStates.confirm_profile)
async def confirm_profile(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_order":
        await handle_cancel_order(callback, state)
        return

    if callback.data == "confirm_yes":
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

            await callback.message.edit_text(  # type: ignore
                f"📍 <b>Адрес доставки:</b>\n\n"
                f"🏠 {address_str}\n\n"
                f"Адрес доставки корректен?",
                reply_markup=get_yes_no_keyboard(),
                parse_mode="HTML",
            )
            await state.set_state(OrderStates.confirm_address)
        else:
            kb = get_addresses_keyboard_order(addresses)
            await callback.message.edit_text(  # type: ignore
                "📍 <b>Выбор адреса доставки</b>\n\n"
                "Выберите один из ваших сохранённых адресов:",
                reply_markup=kb,
                parse_mode="HTML",
            )
            await state.set_state(OrderStates.choosing_address)
    elif callback.data == "confirm_no":
        await callback.message.edit_text(  # type: ignore
            "🚫 <b>Оформление заказа отменено</b>\n\n"
            "Используйте команду /profile для редактирования ваших данных, "
            "затем снова отправьте /order для оформления заказа.",
            reply_markup=None,
        )
        await state.clear()


@order_router.callback_query(OrderStates.choosing_address)
async def choose_address(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_order":
        await handle_cancel_order(callback, state)
        return

    if callback.data and callback.data.startswith("address_order_"):
        try:
            address_id = int(callback.data.split("_")[2])
        except (IndexError, ValueError):
            await callback.message.edit_text("❌ Ошибка в данных адреса!")  # type: ignore
            return

        data = await state.get_data()
        addresses = data.get("addresses", [])

        address = next((a for a in addresses if a["id"] == address_id), None)

        if not address:
            await callback.message.edit_text("❌ Адрес не найден!")  # type: ignore
            return

        await state.update_data(address_id=address["id"], address_full=address)

        async with db_connection.get_session() as session:
            order_service = OrderService(OrderRepo(session), AdminSettingsRepo(session))
            address_str = order_service.format_address(address)

        await callback.message.edit_text(  # type: ignore
            f"📍 <b>Выбранный адрес доставки:</b>\n\n"
            f"🏠 {address_str}\n\n"
            f"Подтверждаете выбор этого адреса?",
            reply_markup=get_yes_no_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(OrderStates.confirm_address)


@order_router.callback_query(OrderStates.confirm_address)
async def confirm_address(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_order":
        await handle_cancel_order(callback, state)
        return

    if callback.data == "confirm_yes":
        await callback.message.edit_text(  # type: ignore
            "🔗 <b>Ссылка на товар</b>\n\n"
            "Отправьте ссылку на товар, который хотите заказать:",
            reply_markup=get_cancel_keyboard(),
        )
        await state.set_state(OrderStates.waiting_for_url)
    elif callback.data == "confirm_no":
        data = await state.get_data()
        addresses = data.get("addresses", [])
        kb = get_addresses_keyboard_order(addresses)
        await callback.message.edit_text(  # type: ignore
            "📍 <b>Выбор адреса доставки</b>\n\n" "Выберите другой адрес из списка:",
            reply_markup=kb,
            parse_mode="HTML",
        )
        await state.set_state(OrderStates.choosing_address)


@order_router.message(OrderStates.waiting_for_url, F.text)
async def get_url(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer(
            "❌ <b>Пустое сообщение</b>\n\n" "Пожалуйста, отправьте ссылку на товар.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    url = message.text.strip()

    if not url:
        await message.answer(
            "❌ <b>Пустая ссылка</b>\n\n"
            "Пожалуйста, введите корректную ссылку на товар.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    if not is_valid_url(url):
        await message.answer(
            "❌ <b>Некорректная ссылка</b>\n\n"
            "Пожалуйста, введите корректную ссылку (должна начинаться с http:// или https://).",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    await state.update_data(product_url=url)
    await message.answer(
        f"🔗 <b>Проверка ссылки на товар</b>\n\n"
        f"Ваша ссылка: {url}\n\n"
        f"Ссылка корректна?",
        reply_markup=get_yes_no_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OrderStates.confirm_url)


@order_router.message(OrderStates.waiting_for_url)
async def url_invalid_format(message: types.Message, state: FSMContext):
    await message.answer(
        "❌ <b>Неверный формат</b>\n\n"
        "Пожалуйста, отправьте ссылку на товар текстовым сообщением.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@order_router.callback_query(OrderStates.confirm_url)
async def confirm_url(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_order":
        await handle_cancel_order(callback, state)
        return

    if callback.data == "confirm_yes":
        await callback.message.edit_text(  # type: ignore
            "📂 <b>Выбор категории товара</b>\n\n"
            "Выберите основную категорию вашего товара:",
            reply_markup=get_main_categories_keyboard_order(),
            parse_mode="HTML",
        )
        await state.set_state(OrderStates.waiting_for_main_category)
    elif callback.data == "confirm_no":
        await callback.message.edit_text(  # type: ignore
            "🔗 <b>Ссылка на товар</b>\n\n" "Отправьте ссылку на товар ещё раз:",
            reply_markup=get_cancel_keyboard(),
        )
        await state.set_state(OrderStates.waiting_for_url)


@order_router.callback_query(OrderStates.waiting_for_main_category)
async def main_category_selected(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_order":
        await handle_cancel_order(callback, state)
        return

    if callback.data and callback.data.startswith("maincat_"):
        try:
            main_cat_id = callback.data.split("_")[1]
        except IndexError:
            await callback.message.edit_text("❌ Ошибка в данных категории!")  # type: ignore
            return

        await state.update_data(main_cat_id=main_cat_id)

        if not CategoryHelper.has_subcategories(main_cat_id):
            await state.update_data(sub_cat_id=None)
            await callback.message.edit_text(  # type: ignore
                "📸 <b>Фотография товара</b>\n\n"
                "Пришлите скриншот или фотографию товара для администратора:",
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML",
            )
            await state.set_state(OrderStates.waiting_for_photo)
        else:
            subcategories_kb = get_subcategories_keyboard_order(main_cat_id)
            await callback.message.edit_text(  # type: ignore
                "📂 <b>Выбор подкатегории</b>\n\n" "Выберите подкатегорию товара:",
                reply_markup=subcategories_kb,
                parse_mode="HTML",
            )
            await state.set_state(OrderStates.waiting_for_subcategory)


@order_router.callback_query(OrderStates.waiting_for_subcategory)
async def subcategory_selected(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_order":
        await handle_cancel_order(callback, state)
        return

    if callback.data == "back_to_main_categories":
        await callback.message.edit_text(  # type: ignore
            "📂 <b>Выбор категории товара</b>\n\n"
            "Выберите основную категорию вашего товара:",
            reply_markup=get_main_categories_keyboard_order(),
            parse_mode="HTML",
        )
        await state.set_state(OrderStates.waiting_for_main_category)
        return

    if callback.data and callback.data.startswith("subcat_"):
        try:
            parts = callback.data.split("_")
            if len(parts) >= 3:
                sub_cat_id = parts[2]
                await state.update_data(sub_cat_id=sub_cat_id)
                await callback.message.edit_text(  # type: ignore
                    "📸 <b>Фотография товара</b>\n\n"
                    "Пришлите скриншот или фотографию товара для администратора:",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode="HTML",
                )
                await state.set_state(OrderStates.waiting_for_photo)
        except (IndexError, ValueError):
            await callback.message.edit_text("❌ Ошибка в данных подкатегории!")  # type: ignore


@order_router.message(OrderStates.waiting_for_photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer(
            "❌ <b>Ошибка получения фото</b>\n\n"
            "Пожалуйста, отправьте фотографию ещё раз.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    photo = message.photo[-1]
    file_id = photo.file_id

    await state.update_data(photo_url=file_id)
    await message.answer(
        "💴 <b>Цена товара</b>\n\n"
        "Укажите цену товара в китайских юанях (например: 150 или 150.50):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OrderStates.waiting_for_price)


@order_router.message(OrderStates.waiting_for_photo)
async def photo_not_sent(message: types.Message, state: FSMContext):
    await message.answer(
        "❌ <b>Требуется фотография</b>\n\n"
        "Пожалуйста, отправьте фотографию товара. Это поможет администратору лучше понять ваш заказ.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@order_router.message(OrderStates.waiting_for_price, F.text)
async def get_price(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer(
            "❌ <b>Пустое сообщение</b>\n\n" "Введите цену товара в китайских юанях.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    price_text = message.text.strip()
    if not price_text:
        await message.answer(
            "❌ <b>Пустая цена</b>\n\n" "Введите корректную цену товара.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    valid, price_yuan = CategoryHelper.validate_price(price_text)

    if not valid:
        await message.answer(
            "❌ <b>Некорректная цена</b>\n\n"
            "Введите корректную цену (число больше 0). Используйте точку или запятую для десятичных дробей.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    await state.update_data(unit_price_yuan=price_yuan)

    data = await state.get_data()
    main_cat_id = data.get("main_cat_id")
    sub_cat_id = data.get("sub_cat_id")

    async with db_connection.get_session() as session:
        order_service = OrderService(OrderRepo(session), AdminSettingsRepo(session))
        price_rub = await order_service.calculate_price_in_rubles(
            price_yuan, main_cat_id, sub_cat_id  # type: ignore
        )

    await state.update_data(unit_price_rub=price_rub)

    await message.answer(
        f"💴 <b>Подтверждение цены</b>\n\n"
        f"Цена товара: <b>{price_yuan} юаней</b>\n"
        f"Примерно: <b>{price_rub:.2f} рублей</b>\n\n"
        f"Цена указана верно?",
        reply_markup=get_yes_no_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OrderStates.confirm_price)


@order_router.message(OrderStates.waiting_for_price)
async def price_invalid_format(message: types.Message, state: FSMContext):
    await message.answer(
        "❌ <b>Неверный формат</b>\n\n"
        "Пожалуйста, отправьте цену товара текстовым сообщением.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@order_router.callback_query(OrderStates.confirm_price)
async def confirm_price(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_order":
        await handle_cancel_order(callback, state)
        return

    if callback.data == "confirm_yes":
        await callback.message.edit_text(  # type: ignore
            "🔢 <b>Количество товара</b>\n\n"
            "Сколько единиц товара вы хотите заказать?",
            reply_markup=get_quantity_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(OrderStates.waiting_for_quantity)
    elif callback.data == "confirm_no":
        await callback.message.edit_text(  # type: ignore
            "💴 <b>Цена товара</b>\n\n"
            "Укажите цену товара в китайских юанях ещё раз:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(OrderStates.waiting_for_price)


@order_router.callback_query(OrderStates.waiting_for_quantity)
async def get_quantity_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_order":
        await handle_cancel_order(callback, state)
        return

    if callback.data in ["quantity_1", "quantity_2"]:
        try:
            quantity = int(callback.data.split("_")[1])
        except (IndexError, ValueError):
            await callback.message.edit_text("❌ Ошибка в данных количества!")  # type: ignore
            return

        await state.update_data(quantity=quantity)
        await callback.message.edit_text(  # type: ignore
            "📝 <b>Описание товара</b>\n\n"
            "Опишите товар подробнее: размер, цвет, модель и другие важные характеристики:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(OrderStates.waiting_for_description)
    elif callback.data == "quantity_other":
        await callback.message.edit_text(  # type: ignore
            "🔢 <b>Количество товара</b>\n\n"
            "Введите нужное количество товара (целое число):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(OrderStates.waiting_for_quantity_text)


@order_router.message(OrderStates.waiting_for_quantity_text, F.text)
async def get_quantity_text(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer(
            "❌ <b>Пустое сообщение</b>\n\n" "Введите количество товара числом.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    quantity_text = message.text.strip()
    if not quantity_text:
        await message.answer(
            "❌ <b>Пустое количество</b>\n\n" "Введите корректное количество товара.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    valid, quantity = CategoryHelper.validate_quantity(quantity_text)

    if not valid:
        await message.answer(
            "❌ <b>Некорректное количество</b>\n\n"
            "Введите корректное количество (целое число больше 0).",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    await state.update_data(quantity=quantity)
    await message.answer(
        "📝 <b>Описание товара</b>\n\n"
        "Опишите товар подробнее: размер, цвет, модель и другие важные характеристики:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OrderStates.waiting_for_description)


@order_router.message(OrderStates.waiting_for_quantity_text)
async def quantity_invalid_format(message: types.Message, state: FSMContext):
    await message.answer(
        "❌ <b>Неверный формат</b>\n\n"
        "Пожалуйста, отправьте количество товара текстовым сообщением.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@order_router.message(OrderStates.waiting_for_description, F.text)
async def get_description(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer(
            "❌ <b>Пустое сообщение</b>\n\n" "Опишите товар подробнее.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    desc = message.text.strip()
    if not desc:
        await message.answer(
            "❌ <b>Пустое описание</b>\n\n" "Пожалуйста, опишите товар подробнее.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    await state.update_data(description=desc)

    await message.answer(
        f"📝 <b>Подтверждение описания</b>\n\n"
        f"Ваше описание товара:\n"
        f"<i>{desc}</i>\n\n"
        f"Описание корректно?",
        reply_markup=get_yes_no_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OrderStates.confirm_description)


@order_router.message(OrderStates.waiting_for_description)
async def description_invalid_format(message: types.Message, state: FSMContext):
    await message.answer(
        "❌ <b>Неверный формат</b>\n\n"
        "Пожалуйста, отправьте описание товара текстовым сообщением.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@order_router.callback_query(OrderStates.confirm_description)
async def confirm_description(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_order":
        await handle_cancel_order(callback, state)
        return

    if callback.data == "confirm_yes":
        await show_order_review(callback, state)
    elif callback.data == "confirm_no":
        await callback.message.edit_text(  # type: ignore
            "📝 <b>Описание товара</b>\n\n"
            "Опишите товар ещё раз, указав все важные детали:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(OrderStates.waiting_for_description)


async def show_order_review(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    async with db_connection.get_session() as session:
        order_service = OrderService(OrderRepo(session), AdminSettingsRepo(session))
        review_text = order_service.format_order_review(data)

    review_text = "📋 <b>Проверка заказа перед отправкой</b>\n\n" + review_text

    photo_url = data.get("photo_url")
    if photo_url:
        await state.update_data(original_message_id=callback.message.message_id)  # type: ignore
        await callback.message.delete()  # type: ignore
        sent_message = await callback.bot.send_photo(  # type: ignore
            chat_id=callback.from_user.id,
            photo=photo_url,
            caption=review_text,
            reply_markup=get_comment_or_send_keyboard(),
            parse_mode="HTML",
        )
        await state.update_data(review_message_id=sent_message.message_id)
    else:
        await callback.message.edit_text(  # type: ignore
            review_text,
            reply_markup=get_comment_or_send_keyboard(),
            parse_mode="HTML",
        )
        await state.update_data(review_message_id=callback.message.message_id)  # type: ignore

    await state.set_state(OrderStates.waiting_for_admin_comment)


@order_router.callback_query(OrderStates.waiting_for_admin_comment)
async def order_admin_comment(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel_order":
        await handle_cancel_order(callback, state)
        return

    if callback.data == "add_comment":
        data = await state.get_data()
        review_message_id = data.get("review_message_id")

        if review_message_id:
            try:
                await callback.bot.edit_message_text(  # type: ignore
                    chat_id=callback.from_user.id,
                    message_id=review_message_id,
                    text="💬 <b>Комментарий для администратора</b>\n\n"
                    "Введите дополнительные пожелания или комментарии для администратора:",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode="HTML",
                )
            except Exception:
                await callback.bot.send_message(  # type: ignore
                    chat_id=callback.from_user.id,
                    text="💬 <b>Комментарий для администратора</b>\n\n"
                    "Введите дополнительные пожелания или комментарии для администратора:",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode="HTML",
                )

        await state.set_state(OrderStates.waiting_for_admin_comment_text)
        return

    if callback.data == "send_order":
        data = await state.get_data()

        async with db_connection.get_session() as session:
            order_service = OrderService(OrderRepo(session), AdminSettingsRepo(session))

            success, message_text = await order_service.submit_order(
                callback.bot, callback.from_user.id, data  # type: ignore
            )

            if success:
                success_text = (
                    "🎉 <b>Заказ успешно оформлен!</b>\n\n"
                    "✅ Ваш заказ отправлен администратору\n"
                    "⏰ Мы свяжемся с вами в ближайшее время\n"
                    "📞 Ожидайте звонка или сообщения\n\n"
                    "Спасибо за выбор нашего сервиса! 🙏"
                )
            else:
                success_text = (
                    "❌ <b>Ошибка при оформлении заказа</b>\n\n"
                    "Произошла техническая ошибка. Пожалуйста, попробуйте ещё раз или обратитесь в поддержку."
                )

            review_message_id = data.get("review_message_id")
            if review_message_id:
                try:
                    await callback.bot.edit_message_text(  # type: ignore
                        chat_id=callback.from_user.id,  # type: ignore
                        message_id=review_message_id,
                        text=success_text,
                        parse_mode="HTML",
                        reply_markup=None,
                    )
                except Exception:
                    await callback.bot.send_message(  # type: ignore
                        chat_id=callback.from_user.id,
                        text=success_text,
                        parse_mode="HTML",
                    )
            else:
                try:
                    await callback.message.edit_text(  # type: ignore
                        success_text, parse_mode="HTML", reply_markup=None
                    )
                except Exception:
                    await callback.bot.send_message(  # type: ignore
                        chat_id=callback.from_user.id,
                        text=success_text,
                        parse_mode="HTML",
                    )

        await state.clear()
        return


@order_router.message(OrderStates.waiting_for_admin_comment_text, F.text)
async def admin_comment_text(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer(
            "❌ <b>Пустое сообщение</b>\n\n" "Введите комментарий для администратора.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    comment = message.text.strip()
    if not comment:
        await message.answer(
            "❌ <b>Пустой комментарий</b>\n\n"
            "Пожалуйста, введите комментарий для администратора.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    await state.update_data(admin_comment=comment)

    sent_message = await message.answer(
        "✅ <b>Комментарий добавлен</b>\n\n"
        "Ваш комментарий сохранён. Теперь можете отправить заказ администратору.",
        reply_markup=get_send_order_keyboard(),
        parse_mode="HTML",
    )

    await state.update_data(review_message_id=sent_message.message_id)
    await state.set_state(OrderStates.waiting_for_admin_comment)


@order_router.message(OrderStates.waiting_for_admin_comment_text)
async def admin_comment_invalid_format(message: types.Message, state: FSMContext):
    await message.answer(
        "❌ <b>Неверный формат</b>\n\n"
        "Пожалуйста, отправьте комментарий текстовым сообщением.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
