from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.repositories import UserRepo
from app.configs import db_connection
from app.keyboards import get_profile_keyboard, get_edit_profile_keyboard
from app.states import ProfileStates
from app.utils import is_valid_phone
from app.services import ProfileService

profile_router = Router()


@profile_router.message(Command("profile"))
async def show_profile(message: types.Message):
    async with db_connection.get_session() as session:
        service = ProfileService(UserRepo(session))
        user = await service.get_user(message.from_user.id)  # type: ignore
        text = service.render_profile(user)
        await message.answer(
            text, reply_markup=get_profile_keyboard(), parse_mode="HTML"
        )


@profile_router.callback_query(F.data == "profile_edit")
async def start_edit_profile(callback: types.CallbackQuery, state: FSMContext):
    async with db_connection.get_session() as session:
        service = ProfileService(UserRepo(session))
        user = await service.get_user(callback.from_user.id)
        profile_text = service.render_profile(user)
        if not await service.is_profile_complete(user):
            await callback.message.edit_reply_markup()  # type: ignore
            await callback.message.edit_text(  # type: ignore
                f"{profile_text}\n\n📝 Введите ваше имя:", parse_mode="HTML"
            )
            await state.set_state(ProfileStates.waiting_for_name)
        else:
            await callback.message.edit_reply_markup()  # type: ignore
            await callback.message.edit_text(  # type: ignore
                f"{profile_text}\n\n✏️ Выберите что хотите изменить:",
                reply_markup=get_edit_profile_keyboard(),
                parse_mode="HTML",
            )


@profile_router.callback_query(F.data.startswith("edit_"))
async def handle_edit_choice(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]  # type: ignore
    await callback.message.edit_reply_markup()  # type: ignore
    if action == "name":
        await callback.message.answer(  # type: ignore
            "📝 Введите новое имя:", parse_mode="HTML"
        )
        await state.set_state(ProfileStates.waiting_for_name)
    elif action == "phone":
        await callback.message.answer(  # type: ignore
            "📱 Введите новый телефон:", parse_mode="HTML"
        )
        await state.set_state(ProfileStates.waiting_for_phone)


@profile_router.message(ProfileStates.waiting_for_name)
async def set_name(message: types.Message, state: FSMContext):
    name = message.text.strip()  # type: ignore
    if not name:
        await message.answer("❌ Имя не может быть пустым!")
        return
    async with db_connection.get_session() as session:
        service = ProfileService(UserRepo(session))
        user = await service.get_user(message.from_user.id)  # type: ignore
        tg_id = message.from_user.id  # type: ignore
        tg_username = message.from_user.username or ""  # type: ignore
        if user and user.phone:
            updated_user = await service.update_name(tg_id, tg_username, name)
            text = service.render_profile(updated_user)
            await message.answer(
                text, reply_markup=get_profile_keyboard(), parse_mode="HTML"
            )
            await state.clear()
        else:
            await state.update_data(name=name)
            await message.answer("📱 Теперь введите ваш телефон:", parse_mode="HTML")
            await state.set_state(ProfileStates.waiting_for_phone)


@profile_router.message(ProfileStates.waiting_for_phone)
async def set_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()  # type: ignore
    if not is_valid_phone(phone):
        await message.answer(
            "❌ Некорректный формат телефона!\n"
            "Примеры:\n"
            "<code>+79261234567</code>\n"
            "<code>89261234567</code>",
            parse_mode="HTML",
        )
        return
    async with db_connection.get_session() as session:
        service = ProfileService(UserRepo(session))
        tg_id = message.from_user.id  # type: ignore
        tg_username = message.from_user.username or ""  # type: ignore
        data = await state.get_data()
        user = await service.get_user(tg_id)
        if user and user.name:
            updated_user = await service.update_phone(tg_id, tg_username, phone)
            text = service.render_profile(updated_user)
            await message.answer(
                text, reply_markup=get_profile_keyboard(), parse_mode="HTML"
            )
            await state.clear()
        else:
            name = data.get("name", "")
            new_user = await service.create_user(tg_id, tg_username, name, phone)
            text = service.render_profile(new_user)
            await message.answer(
                text, reply_markup=get_profile_keyboard(), parse_mode="HTML"
            )
            await state.clear()


@profile_router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    async with db_connection.get_session() as session:
        service = ProfileService(UserRepo(session))
        user = await service.get_user(callback.from_user.id)
        text = service.render_profile(user)
        await callback.message.edit_reply_markup()  # type: ignore
        await callback.message.edit_text(  # type: ignore
            text, reply_markup=get_profile_keyboard(), parse_mode="HTML"
        )
