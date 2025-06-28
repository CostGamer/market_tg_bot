from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.repositories import AddressRepo, UserRepo
from app.configs import db_connection
from app.keyboards import (
    get_addresses_keyboard,
    get_profile_keyboard,
    get_address_manage_keyboard,
    get_confirmation_keyboard,
)
from app.states import AddressStates, ProfileStates
from app.models.pydantic_models import AddressPM
from app.services import ProfileService

addresses_router = Router()

MAX_ADDRESSES = 3


@addresses_router.message(Command("addresses"))
async def show_addresses_command(message: types.Message, state: FSMContext):
    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)
        addresses = await address_repo.get_user_addresses(message.from_user.id)  # type: ignore

        if addresses is None:
            addresses = []

        if len(addresses) == 0:  # type: ignore
            profile_service = ProfileService(UserRepo(session))
            user = await profile_service.get_user(message.from_user.id)  # type: ignore
            if not user or not user.name or not user.phone:
                await message.answer(
                    "⚠️ Перед добавлением адреса заполните профиль.\n"
                    "А затем заново выполните команду /addresses",
                    reply_markup=get_profile_keyboard(),
                )
                await message.answer("📝 Введите ваше имя:")
                await state.set_state(ProfileStates.waiting_for_name)
                return

            await message.answer("🏙️ Введите город пункта выдачи:")
            await state.set_state(AddressStates.waiting_for_city)
        else:
            keyboard = get_addresses_keyboard(addresses)
            text = f"🏠 Ваши адреса ({len(addresses)}/{MAX_ADDRESSES}):"  # type: ignore
            await message.answer(text, reply_markup=keyboard)
            await state.set_state(AddressStates.choosing_address)


@addresses_router.callback_query(AddressStates.choosing_address)
async def choose_address(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "add_address":
        async with db_connection.get_session() as session:
            address_repo = AddressRepo(session)
            addresses = await address_repo.get_user_addresses(callback.from_user.id)

            if addresses is None:
                addresses = []

            if len(addresses) >= MAX_ADDRESSES:  # type: ignore
                await callback.message.edit_text(  # type: ignore
                    f"⚠️ Достигнут лимит адресов!\n\n"
                    f"Вы можете иметь максимум {MAX_ADDRESSES} адресов. "
                    f"Удалите один из существующих адресов, чтобы добавить новый.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="⬅️ Назад к списку",
                                    callback_data="back_to_list",
                                )
                            ]
                        ]
                    ),
                )
                return

            profile_service = ProfileService(UserRepo(session))
            user = await profile_service.get_user(callback.from_user.id)
            if not user or not user.name or not user.phone:
                await callback.message.edit_text(  # type: ignore
                    "⚠️ Перед добавлением адреса заполните профиль.\n"
                    "А затем заново выполните команду /addresses",
                    reply_markup=get_profile_keyboard(),
                )
                await callback.message.answer("📝 Введите ваше имя:")  # type: ignore
                await state.set_state(ProfileStates.waiting_for_name)
                return

        await callback.message.edit_text("🏙️ Введите город пункта выдачи:")  # type: ignore
        await state.set_state(AddressStates.waiting_for_city)
        return

    if callback.data == "back_to_list":
        async with db_connection.get_session() as session:
            address_repo = AddressRepo(session)
            addresses = await address_repo.get_user_addresses(callback.from_user.id)

            if addresses is None:
                addresses = []

            keyboard = get_addresses_keyboard(addresses)

            if len(addresses) == 0:  # type: ignore
                text = "📭 У вас пока нет сохранённых адресов"
            else:
                text = f"🏠 Ваши адреса ({len(addresses)}/{MAX_ADDRESSES}):"  # type: ignore

            await callback.message.edit_text(text, reply_markup=keyboard)  # type: ignore
            await state.set_state(AddressStates.choosing_address)
        return

    if callback.data.startswith("address_"):  # type: ignore
        address_id = int(callback.data.split("_")[1])  # type: ignore
        async with db_connection.get_session() as session:
            address_repo = AddressRepo(session)
            addresses = await address_repo.get_user_addresses(callback.from_user.id)

            if addresses is None:
                addresses = []

            address = next((a for a in addresses if a.id == address_id), None)  # type: ignore
            if address:
                await state.update_data(selected_address_id=address.id)
                keyboard = get_address_manage_keyboard()
                await callback.message.edit_text(  # type: ignore
                    f"📍 <b>Выбранный адрес:</b>\n\n"
                    f"🏙️ <b>Город:</b> {address.city}\n"
                    f"🏠 <b>Адрес:</b> {address.address}\n"
                    f"📮 <b>Индекс:</b> {address.index}\n"
                    f"🏷️ <b>Название:</b> {address.name}",
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
                await state.set_state(AddressStates.manage_address)
            else:
                await callback.message.edit_text("❌ Адрес не найден!")  # type: ignore


@addresses_router.callback_query(AddressStates.manage_address)
async def manage_address(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    address_id = data.get("selected_address_id")

    if callback.data == "delete_address":
        async with db_connection.get_session() as session:
            address_repo = AddressRepo(session)
            await address_repo.delete_address(address_id)  # type: ignore
            await callback.message.edit_text("🗑️ Адрес успешно удалён!")  # type: ignore
            addresses = await address_repo.get_user_addresses(callback.from_user.id)

            if addresses is None:
                addresses = []

            if len(addresses) == 0:  # type: ignore
                await callback.message.edit_text("🏙️ Введите город пункта выдачи:")  # type: ignore
                await state.set_state(AddressStates.waiting_for_city)
            else:
                keyboard = get_addresses_keyboard(addresses)
                text = f"🏠 Ваши адреса ({len(addresses)}/{MAX_ADDRESSES}):"  # type: ignore
                await callback.message.edit_text(text, reply_markup=keyboard)  # type: ignore
                await state.set_state(AddressStates.choosing_address)
    elif callback.data == "back_to_addresses":
        async with db_connection.get_session() as session:
            address_repo = AddressRepo(session)
            addresses = await address_repo.get_user_addresses(callback.from_user.id)

            if addresses is None:
                addresses = []

            keyboard = get_addresses_keyboard(addresses)

            if len(addresses) == 0:  # type: ignore
                text = "📭 У вас пока нет сохранённых адресов"
            else:
                text = f"🏠 Ваши адреса ({len(addresses)}/{MAX_ADDRESSES}):"  # type: ignore

            await callback.message.edit_text(text, reply_markup=keyboard)  # type: ignore
            await state.set_state(AddressStates.choosing_address)


@addresses_router.message(AddressStates.waiting_for_city)
async def address_city(message: types.Message, state: FSMContext):
    city = message.text.strip()  # type: ignore
    if not city:
        await message.answer("❌ Город не может быть пустым! Попробуйте ещё раз:")
        return

    await state.update_data(city=city)
    keyboard = get_confirmation_keyboard()
    await message.answer(
        f"🏙️ <b>Город:</b> {city}\n\n" f"Всё верно?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(AddressStates.confirm_city)


@addresses_router.callback_query(AddressStates.confirm_city)
async def confirm_city(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "confirm_yes":
        await callback.message.edit_text(  # type: ignore
            "🏠 Введите адрес пункта выдачи (улица, дом, офис):"
        )
        await state.set_state(AddressStates.waiting_for_address)
    elif callback.data == "confirm_no":
        await callback.message.edit_text("🏙️ Введите город пункта выдачи:")  # type: ignore
        await state.set_state(AddressStates.waiting_for_city)


@addresses_router.message(AddressStates.waiting_for_address)
async def address_address(message: types.Message, state: FSMContext):
    address = message.text.strip()  # type: ignore
    if not address:
        await message.answer("❌ Адрес не может быть пустым! Попробуйте ещё раз:")
        return

    await state.update_data(address=address)
    keyboard = get_confirmation_keyboard()
    await message.answer(
        f"🏠 <b>Адрес:</b> {address}\n\n" f"Всё верно?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(AddressStates.confirm_address)


@addresses_router.callback_query(AddressStates.confirm_address)
async def confirm_address(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "confirm_yes":
        await callback.message.edit_text("📮 Введите почтовый индекс (6 цифр):")  # type: ignore
        await state.set_state(AddressStates.waiting_for_index)
    elif callback.data == "confirm_no":
        await callback.message.edit_text(  # type: ignore
            "🏠 Введите адрес пункта выдачи (улица, дом, офис):"
        )
        await state.set_state(AddressStates.waiting_for_address)


@addresses_router.message(AddressStates.waiting_for_index)
async def address_index(message: types.Message, state: FSMContext):
    index = message.text.strip()  # type: ignore

    if not index.isdigit():
        await message.answer(
            "❌ Индекс должен состоять только из цифр! Попробуйте ещё раз:"
        )
        return
    if len(index) != 6:
        await message.answer(
            "❌ Индекс должен содержать ровно 6 цифр! Попробуйте ещё раз:"
        )
        return
    if index == "000000":
        await message.answer("❌ Введите корректный индекс! Попробуйте ещё раз:")
        return

    await state.update_data(index=int(index))
    keyboard = get_confirmation_keyboard()
    await message.answer(
        f"📮 <b>Индекс:</b> {index}\n\n" f"Всё верно?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(AddressStates.confirm_index)


@addresses_router.callback_query(AddressStates.confirm_index)
async def confirm_index(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "confirm_yes":
        await callback.message.edit_text(  # type: ignore
            "🏷️ Введите название пункта выдачи\n"
            "(например: 'Boxberry Центральный', 'СДЭК на Ленина'):"
        )
        await state.set_state(AddressStates.waiting_for_name)
    elif callback.data == "confirm_no":
        await callback.message.edit_text("📮 Введите почтовый индекс (6 цифр):")  # type: ignore
        await state.set_state(AddressStates.waiting_for_index)


@addresses_router.message(AddressStates.waiting_for_name)
async def address_name(message: types.Message, state: FSMContext):
    name = message.text.strip()  # type: ignore
    if not name:
        await message.answer("❌ Название не может быть пустым! Попробуйте ещё раз:")
        return

    await state.update_data(name=name)
    keyboard = get_confirmation_keyboard()
    await message.answer(
        f"🏷️ <b>Название:</b> {name}\n\n" f"Всё верно?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(AddressStates.confirm_name)


@addresses_router.callback_query(AddressStates.confirm_name)
async def confirm_name(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "confirm_yes":
        data = await state.get_data()

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Сохранить адрес", callback_data="save_address"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отменить", callback_data="cancel_address"
                    )
                ],
            ]
        )

        await callback.message.edit_text(  # type: ignore
            f"📋 <b>Проверьте данные адреса:</b>\n\n"
            f"🏙️ <b>Город:</b> {data['city']}\n"
            f"🏠 <b>Адрес:</b> {data['address']}\n"
            f"📮 <b>Индекс:</b> {data['index']}\n"
            f"🏷️ <b>Название:</b> {data['name']}\n\n"
            f"Сохранить этот адрес?",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        await state.set_state(AddressStates.final_confirmation)
    elif callback.data == "confirm_no":
        await callback.message.edit_text(  # type: ignore
            "🏷️ Введите название пункта выдачи\n"
            "(например: 'Boxberry Центральный', 'СДЭК на Ленина'):"
        )
        await state.set_state(AddressStates.waiting_for_name)


@addresses_router.callback_query(AddressStates.final_confirmation)
async def final_confirmation(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "save_address":
        data = await state.get_data()
        address_data = AddressPM(
            address=data["address"],
            city=data["city"],
            index=data["index"],
            name=data["name"],
        )

        async with db_connection.get_session() as session:
            address_repo = AddressRepo(session)
            new_address = await address_repo.create_address(
                callback.from_user.id, address_data
            )

            if new_address:
                await callback.message.edit_text("✅ Адрес успешно сохранён!")  # type: ignore
                addresses = await address_repo.get_user_addresses(callback.from_user.id)

                # Проверяем, что addresses не None
                if addresses is None:
                    addresses = []

                keyboard = get_addresses_keyboard(addresses)

                text = f"🏠 Ваши адреса ({len(addresses)}/{MAX_ADDRESSES}):"  # type: ignore
                await callback.message.answer(text, reply_markup=keyboard)  # type: ignore
                await state.set_state(AddressStates.choosing_address)
            else:
                await callback.message.edit_text(  # type: ignore
                    "❌ Ошибка при сохранении адреса! Попробуйте ещё раз."
                )
                await state.clear()
    elif callback.data == "cancel_address":
        await callback.message.edit_text("❌ Добавление адреса отменено.")  # type: ignore
        await state.clear()
