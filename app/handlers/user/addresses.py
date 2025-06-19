from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from app.repositories import AddressRepo, UserRepo
from app.configs import db_connection
from app.keyboards import (
    get_addresses_keyboard,
    get_address_manage_keyboard,
    get_edit_address_field_keyboard,
    get_profile_keyboard,
)
from app.states import AddressStates, ProfileStates
from app.models.pydantic_models import AddressPM
from app.services import ProfileService

addresses_router = Router()


@addresses_router.message(Command("addresses"))
async def show_addresses_command(message: types.Message, state: FSMContext):
    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)
        addresses = await address_repo.get_user_addresses(message.from_user.id)  # type: ignore
        keyboard = get_addresses_keyboard(addresses)
        await message.answer("🏠 Ваши адреса:", reply_markup=keyboard)
    await state.set_state(AddressStates.choosing_address)


@addresses_router.message(AddressStates.choosing_address)
async def choose_address(message: types.Message, state: FSMContext):
    text = message.text.strip()  # type: ignore
    if text == "➕ Добавить адрес":
        async with db_connection.get_session() as session:
            profile_service = ProfileService(UserRepo(session))
            user = await profile_service.get_user(message.from_user.id)  # type: ignore
            if not user or not user.name or not user.phone:
                await message.answer(
                    "Перед добавлением адреса заполните профиль.\nА затем заново выполните команду /addresses",
                    reply_markup=get_profile_keyboard(),
                )
                await message.answer("📝 Введите ваше имя:")
                await state.set_state(ProfileStates.waiting_for_name)
                return
        await message.answer(
            "🏙️ Введите город пункта выдачи:", reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(AddressStates.waiting_for_city)
        return
    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)
        addresses = await address_repo.get_user_addresses(message.from_user.id)  # type: ignore
        address = next((a for a in addresses if a.name == text), None)  # type: ignore
        if address:
            await state.update_data(selected_address_id=address.id)
            keyboard = get_address_manage_keyboard()
            await message.answer(
                f"<b>Адрес:</b>\nГород: {address.city}\nАдрес: {address.address}\nИндекс: {address.index}\nНазвание: {address.name}",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            await state.set_state(AddressStates.manage_address)
        else:
            await message.answer("❌ Адрес не найден!")


@addresses_router.message(AddressStates.manage_address)
async def manage_address(message: types.Message, state: FSMContext):
    text = message.text.strip()  # type: ignore
    data = await state.get_data()
    address_id = data.get("selected_address_id")
    if text == "✏️ Изменить":
        keyboard = get_edit_address_field_keyboard()
        await message.answer("✏️ Выберите что хотите изменить:", reply_markup=keyboard)
        await state.set_state(AddressStates.edit_field_choice)
    elif text == "🗑️ Удалить":
        async with db_connection.get_session() as session:
            address_repo = AddressRepo(session)
            await address_repo.delete_address(address_id)  # type: ignore
            await message.answer("✅ Адрес удалён!", reply_markup=ReplyKeyboardRemove())
            addresses = await address_repo.get_user_addresses(message.from_user.id)  # type: ignore
            keyboard = get_addresses_keyboard(addresses)
            await message.answer("🏠 Ваши адреса:", reply_markup=keyboard)
            await state.set_state(AddressStates.choosing_address)
    elif text == "⬅️ Назад":
        async with db_connection.get_session() as session:
            address_repo = AddressRepo(session)
            addresses = await address_repo.get_user_addresses(message.from_user.id)  # type: ignore
            keyboard = get_addresses_keyboard(addresses)
            await message.answer("🏠 Ваши адреса:", reply_markup=keyboard)
            await state.set_state(AddressStates.choosing_address)


@addresses_router.message(AddressStates.edit_field_choice)
async def edit_field_choice(message: types.Message, state: FSMContext):
    text = message.text.strip()  # type: ignore
    field_map = {
        "✏️ Имя": "name",
        "🏙️ Город": "city",
        "🏠 Адрес": "address",
        "🔢 Индекс": "index",
        "❌ Отмена": "cancel",
    }
    field = field_map.get(text)
    if field == "cancel":
        await message.answer(
            "Редактирование отменено.", reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    if field:
        await state.update_data(field=field)
        await message.answer(f"Введите новое значение для поля {field}:")
        await state.set_state(AddressStates.waiting_for_edit_field)
    else:
        await message.answer("Пожалуйста, выберите действие на клавиатуре.")


@addresses_router.message(AddressStates.waiting_for_edit_field)
async def handle_edit_field_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("field")
    address_id = data.get("selected_address_id")
    new_value = message.text.strip()  # type: ignore
    if not new_value:
        await message.answer("❌ Значение не может быть пустым!")
        return
    if field == "index":
        if not (new_value.isdigit() and len(new_value) == 6):
            await message.answer("❌ Индекс должен состоять ровно из 6 цифр!")
            return
        if new_value == "000000":
            await message.answer("❌ Введите корректный индекс!")
            return
    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)
        addresses = await address_repo.get_user_addresses(message.from_user.id)  # type: ignore
        current_address = next((a for a in addresses if a.id == address_id), None)  # type: ignore
        if not current_address:
            await message.answer("❌ Адрес не найден!")
            await state.clear()
            return
        address_data = AddressPM(
            name=current_address.name if field != "name" else new_value,
            city=current_address.city if field != "city" else new_value,
            address=current_address.address if field != "address" else new_value,
            index=(current_address.index if field != "index" else int(new_value)),
        )
        updated = await address_repo.update_address(
            address_id=address_id, address_data=address_data  # type: ignore
        )
        if updated:
            await message.answer(
                "✅ Адрес успешно обновлен!", reply_markup=ReplyKeyboardRemove()
            )
            addresses = await address_repo.get_user_addresses(message.from_user.id)  # type: ignore
            keyboard = get_addresses_keyboard(addresses)
            await message.answer("🏠 Ваши адреса:", reply_markup=keyboard)
            await state.set_state(AddressStates.choosing_address)
        else:
            await message.answer("❌ Ошибка при обновлении адреса!")
            await state.clear()


@addresses_router.message(AddressStates.waiting_for_city)
async def address_city(message: types.Message, state: FSMContext):
    city = message.text.strip()  # type: ignore
    if not city:
        await message.answer("❌ Город не может быть пустым!")
        return
    await state.update_data(city=city)
    await message.answer("🏠 Введите адрес пункта выдачи (улица, дом, офис):")
    await state.set_state(AddressStates.waiting_for_address)


@addresses_router.message(AddressStates.waiting_for_address)
async def address_address(message: types.Message, state: FSMContext):
    address = message.text.strip()  # type: ignore
    if not address:
        await message.answer("❌ Адрес не может быть пустым!")
        return
    await state.update_data(address=address)
    await message.answer("🏷️ Введите индекс пункта выдачи:")
    await state.set_state(AddressStates.waiting_for_index)


@addresses_router.message(AddressStates.waiting_for_index)
async def address_index(message: types.Message, state: FSMContext):
    index = message.text.strip()  # type: ignore
    if not index.isdigit():
        await message.answer("❌ Индекс должен быть числом!")
        return
    if len(index) != 6:
        await message.answer("❌ Индекс должен быть 6 цифр!")
        return
    if index == "000000":
        await message.answer("❌ Введите корректный индекс!")
        return
    await state.update_data(index=int(index))
    await message.answer(
        "🏷️ Введите название пункта выдачи (например, 'Boxberry Центральный'):"
    )
    await state.set_state(AddressStates.waiting_for_name)


@addresses_router.message(AddressStates.waiting_for_name)
async def address_name(message: types.Message, state: FSMContext):
    name = message.text.strip()  # type: ignore
    if not name:
        await message.answer("❌ Название не может быть пустым!")
        return
    await state.update_data(name=name)
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
            message.from_user.id, address_data  # type: ignore
        )
        if new_address:
            await message.answer(
                "✅ Адрес успешно добавлен!", reply_markup=ReplyKeyboardRemove()
            )
            addresses = await address_repo.get_user_addresses(message.from_user.id)  # type: ignore
            keyboard = get_addresses_keyboard(addresses)
            await message.answer("🏠 Ваши адреса:", reply_markup=keyboard)
            await state.set_state(AddressStates.choosing_address)
        else:
            await message.answer("❌ Ошибка при сохранении адреса!")
            await state.clear()
