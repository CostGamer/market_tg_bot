from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from app.repositories import AdminSettingsRepo, UserRepo
from app.configs import db_connection, all_settings
from app.keyboards.support import get_support_faq_keyboard
from app.states import SupportStates
from app.services import ProfileService
from app.utils import is_valid_phone

support_router = Router()


@support_router.message(Command("support"))
async def start_support(message: types.Message, state: FSMContext):
    async with db_connection.get_session() as session:
        repo = AdminSettingsRepo(session)
        settings = await repo.get_settings()
        faq = settings.faq if settings and settings.faq else "FAQ пока не заполнен."

    await message.answer(
        f"Перед тем как обратиться в поддержку, ознакомьтесь с часто задаваемыми вопросами:\n\n"
        f"{faq}\n\n"
        f"Вы нашли ответ на свой вопрос?",
        reply_markup=get_support_faq_keyboard(),
    )
    await state.set_state(SupportStates.waiting_for_faq_confirmation)


@support_router.message(SupportStates.waiting_for_faq_confirmation)
async def after_faq_confirmation(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()  # type: ignore
    if "да" in text:
        await message.answer(
            "Рады, что смогли помочь! Если появятся вопросы — обращайтесь.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()
    elif "нет" in text:
        async with db_connection.get_session() as session:
            service = ProfileService(UserRepo(session))
            user = await service.get_user(message.from_user.id)  # type: ignore
            username = user.tg_username if user and user.tg_username else None
            phone = user.phone if user and user.phone else None

        if username and phone:
            confirm_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="✅ Всё верно")],
                    [KeyboardButton(text="✏️ Изменить данные")],
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            await state.update_data(username=username, phone=phone)
            await message.answer(
                f"Ваши данные для обращения в поддержку:\n"
                f"Username: {username}\n"
                f"Телефон: {phone}\n\n"
                f"Если всё верно — подтвердите, либо выберите изменение.",
                reply_markup=confirm_kb,
            )
            await state.set_state(SupportStates.waiting_for_profile_confirm)
        else:
            skip_kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Пропустить")]],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            await message.answer(
                "Пожалуйста, введите ваш username (например, @username) или нажмите «Пропустить»:",
                reply_markup=skip_kb,
            )
            await state.set_state(SupportStates.waiting_for_username)
    else:
        await message.answer("Пожалуйста, выберите вариант на клавиатуре.")


@support_router.message(SupportStates.waiting_for_profile_confirm)
async def profile_confirm(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()  # type: ignore
    if "верно" in text:
        await message.answer(
            "Опишите ваш вопрос или проблему:", reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(SupportStates.waiting_for_question)
    elif "изменить" in text:
        skip_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Пропустить")]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            "Пожалуйста, введите ваш username (например, @username) или нажмите «Пропустить»:",
            reply_markup=skip_kb,
        )
        await state.set_state(SupportStates.waiting_for_username)
    else:
        await message.answer("Пожалуйста, выберите вариант на клавиатуре.")


@support_router.message(SupportStates.waiting_for_username, F.text)
async def get_support_username(message: types.Message, state: FSMContext):
    username = message.text.strip()  # type: ignore
    if username.lower() in {"-", "пропустить"}:
        username = "не указан"
    elif not username.startswith("@") or len(username) < 3:
        await message.answer(
            "Пожалуйста, введите корректный username, начинающийся с @, или нажмите «Пропустить»."
        )
        return
    await state.update_data(username=username)
    await message.answer(
        "Теперь введите ваш номер телефона (например, +79001234567):",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(SupportStates.waiting_for_phone)


@support_router.message(SupportStates.waiting_for_phone, F.text)
async def get_support_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()  # type: ignore
    if not is_valid_phone(phone):
        await message.answer(
            "Пожалуйста, введите корректный номер телефона в формате +79001234567."
        )
        return
    await state.update_data(phone=phone)
    await message.answer("Опишите ваш вопрос или проблему:")
    await state.set_state(SupportStates.waiting_for_question)


@support_router.message(SupportStates.waiting_for_question, F.text)
async def get_support_question(message: types.Message, state: FSMContext):
    question = message.text.strip()  # type: ignore
    if not question:
        await message.answer("Пожалуйста, опишите ваш вопрос или проблему.")
        return

    data = await state.get_data()
    username = data.get("username")
    phone = data.get("phone")

    support_msg = (
        f"🆘 Новое обращение в поддержку!\n"
        f"Username: {username}\n"
        f"Телефон: {phone}\n"
        f"Вопрос:\n{question}\n"
        f"Telegram ID: {message.from_user.id}"  # type: ignore
    )
    await message.bot.send_message(all_settings.different.support_group_id, support_msg)  # type: ignore
    await message.answer(
        "Ваше обращение отправлено в поддержку. Мы свяжемся с вами в ближайшее время!"
    )
    await state.clear()
