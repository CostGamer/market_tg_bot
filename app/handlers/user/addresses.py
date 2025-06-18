from logging import getLogger
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.repositories import AddressRepo
from app.configs import db_connection
from app.keyboards import (
    get_addresses_keyboard,
    get_address_manage_keyboard,
    get_edit_address_field_keyboard,
)
from app.states import AddressStates
from app.models.pydantic_models import AddressPM

logger = getLogger(__name__)

addresses_router = Router()


@addresses_router.message(Command("addresses"))
async def show_addresses_command(message: types.Message, state: FSMContext):
    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)
        addresses = await address_repo.get_user_addresses(message.from_user.id)
        keyboard = get_addresses_keyboard(addresses)
        await message.answer(
            "🏠 Ваши адреса:", reply_markup=keyboard, parse_mode="HTML"
        )


@addresses_router.callback_query(F.data == "add_address")
async def handle_add_address(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("🏙️ Введите город пункта выдачи:")
    await state.set_state(AddressStates.waiting_for_city)


@addresses_router.message(AddressStates.waiting_for_city)
async def address_city(message: types.Message, state: FSMContext):
    city = message.text.strip()
    if not city:
        await message.answer("❌ Город не может быть пустым!")
        return
    await state.update_data(city=city)
    await message.answer("🏠 Введите адрес пункта выдачи (улица, дом, офис):")
    await state.set_state(AddressStates.waiting_for_address)


@addresses_router.message(AddressStates.waiting_for_address)
async def address_address(message: types.Message, state: FSMContext):
    address = message.text.strip()
    if not address:
        await message.answer("❌ Адрес не может быть пустым!")
        return
    await state.update_data(address=address)
    await message.answer("🏷️ Введите индекс пункта выдачи:")
    await state.set_state(AddressStates.waiting_for_index)


@addresses_router.message(AddressStates.waiting_for_index)
async def address_index(message: types.Message, state: FSMContext):
    index = message.text.strip()
    if not index.isdigit():
        await message.answer("❌ Индекс должен быть числом!")
        return
    await state.update_data(index=int(index))
    await message.answer(
        "🏷️ Введите название пункта выдачи (например, 'Boxberry Центральный'):"
    )
    await state.set_state(AddressStates.waiting_for_name)


@addresses_router.message(AddressStates.waiting_for_name)
async def address_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
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
            message.from_user.id, address_data
        )
        if new_address:
            await message.answer("✅ Адрес успешно добавлен!")
            addresses = await address_repo.get_user_addresses(message.from_user.id)
            keyboard = get_addresses_keyboard(addresses)
            await message.answer(
                "🏠 Ваши адреса:", reply_markup=keyboard, parse_mode="HTML"
            )
        else:
            await message.answer("❌ Ошибка при сохранении адреса!")
    await state.clear()


@addresses_router.callback_query(F.data.startswith("edit_address_"))
async def handle_edit_address(callback: types.CallbackQuery, state: FSMContext):
    address_id = callback.data.replace("edit_address_", "")
    await state.update_data(address_id=address_id)
    await callback.answer()
    await callback.message.edit_text(
        "✏️ Выберите что хотите изменить:",
        reply_markup=get_edit_address_field_keyboard(address_id),
        parse_mode="HTML",
    )


@addresses_router.callback_query(F.data.startswith("edit_field_"))
async def handle_edit_field_choice(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    field_name = parts[2]
    address_id = callback.data.replace(f"edit_field_{field_name}_", "")
    await state.update_data(address_id=address_id, field=field_name)
    field_translation = {
        "name": "название",
        "city": "город",
        "address": "адрес",
        "index": "индекс",
    }
    await callback.answer()
    await callback.message.answer(f"Введите новое {field_translation[field_name]}:")
    await state.set_state(AddressStates.waiting_for_edit_field)


@addresses_router.message(AddressStates.waiting_for_edit_field)
async def handle_edit_field_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data["field"]
    address_id = data["address_id"]
    new_value = message.text.strip()

    if not new_value:
        await message.answer("❌ Значение не может быть пустым!")
        return

    if field == "index":
        if not new_value.isdigit():
            await message.answer("❌ Индекс должен быть числом!")
            return
        new_value = int(new_value)

    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)

        # Получаем текущий адрес для создания полной модели
        addresses = await address_repo.get_user_addresses(message.from_user.id)
        current_address = next((a for a in addresses if str(a.id) == address_id), None)

        if not current_address:
            await message.answer("❌ Адрес не найден!")
            await state.clear()
            return

        # Создаем полную модель с обновленным полем
        address_data = AddressPM(
            name=current_address.name if field != "name" else new_value,
            city=current_address.city if field != "city" else new_value,
            address=current_address.address if field != "address" else new_value,
            index=current_address.index if field != "index" else new_value,
        )

        updated = await address_repo.update_address(
            address_id=address_id, address_data=address_data
        )

        if updated:
            await message.answer("✅ Адрес успешно обновлен!")
            # Показываем обновленный список адресов
            addresses = await address_repo.get_user_addresses(message.from_user.id)
            keyboard = get_addresses_keyboard(addresses)
            await message.answer(
                "🏠 Ваши адреса:", reply_markup=keyboard, parse_mode="HTML"
            )
        else:
            await message.answer("❌ Ошибка при обновлении адреса!")

    await state.clear()


@addresses_router.callback_query(F.data.startswith("delete_address_"))
async def handle_delete_address(callback: types.CallbackQuery, state: FSMContext):
    address_id = callback.data.replace("delete_address_", "")
    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)
        success = await address_repo.delete_address(address_id)
        if success:
            await callback.answer("✅ Адрес удалён!")
            addresses = await address_repo.get_user_addresses(callback.from_user.id)
            keyboard = get_addresses_keyboard(addresses)
            await callback.message.edit_text(
                "🏠 Ваши адреса:", reply_markup=keyboard, parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Адрес не найден!")


@addresses_router.callback_query(F.data.startswith("address_"))
async def handle_address_detail(callback: types.CallbackQuery, state: FSMContext):
    address_id = callback.data.split("_")[1]
    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)
        addresses = await address_repo.get_user_addresses(callback.from_user.id)
        address = next((a for a in addresses if str(a.id) == address_id), None)
        if address:
            text = (
                f"<b>Адрес:</b>\n"
                f"Город: {address.city}\n"
                f"Адрес: {address.address}\n"
                f"Индекс: {address.index}\n"
                f"Название: {address.name}"
            )
            await callback.answer()
            await callback.message.edit_text(
                text,
                reply_markup=get_address_manage_keyboard(address.id),
                parse_mode="HTML",
            )
        else:
            await callback.answer("❌ Адрес не найден!")


@addresses_router.callback_query(F.data == "profile_addresses")
async def return_to_addresses(callback: types.CallbackQuery, state: FSMContext):
    async with db_connection.get_session() as session:
        address_repo = AddressRepo(session)
        addresses = await address_repo.get_user_addresses(callback.from_user.id)
        keyboard = get_addresses_keyboard(addresses)
        await callback.answer()
        await callback.message.edit_text(
            "🏠 Ваши адреса:", reply_markup=keyboard, parse_mode="HTML"
        )
