from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
        "❓ <b>Перед тем как обратиться в поддержку, ознакомьтесь с часто задаваемыми вопросами:</b>\n\n"
        f"{faq}\n\n"
        "🔍 <b>Вы нашли ответ на свой вопрос?</b>",
        reply_markup=get_support_faq_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(SupportStates.waiting_for_faq_confirmation)


@support_router.callback_query(SupportStates.waiting_for_faq_confirmation)
async def after_faq_confirmation(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "faq_found":
        await callback.message.edit_text(  # type: ignore
            "🎉 <b>Рады, что смогли помочь!</b>\n"
            "Если появятся вопросы — смело обращайтесь! 😊",
            parse_mode="HTML",
        )
        await state.clear()
    elif callback.data == "faq_not_found":
        async with db_connection.get_session() as session:
            service = ProfileService(UserRepo(session))
            user = await service.get_user(callback.from_user.id)
            username = user.tg_username if user and user.tg_username else None
            phone = user.phone if user and user.phone else None

        if username and phone:
            confirm_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Всё верно", callback_data="profile_confirm"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="✏️ Изменить данные", callback_data="profile_edit"
                        )
                    ],
                ]
            )
            await state.update_data(username=username, phone=phone)
            await callback.message.edit_text(  # type: ignore
                f"📝 <b>Ваши данные для обращения в поддержку:</b>\n"
                f"👤 Username: <code>{username}</code>\n"
                f"📞 Телефон: <code>{phone}</code>\n\n"
                "✅ <b>Если всё верно — подтвердите, либо выберите изменение.</b>",
                reply_markup=confirm_kb,
                parse_mode="HTML",
            )
            await state.set_state(SupportStates.waiting_for_profile_confirm)
        else:
            skip_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Пропустить", callback_data="skip_username"
                        )
                    ]
                ]
            )
            await callback.message.edit_text(  # type: ignore
                "👤 <b>Пожалуйста, введите ваш username</b> (например, <code>@username</code>) или нажмите «Пропустить»:",
                reply_markup=skip_kb,
                parse_mode="HTML",
            )
            await state.set_state(SupportStates.waiting_for_username)


@support_router.callback_query(SupportStates.waiting_for_profile_confirm)
async def profile_confirm(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "profile_confirm":
        await callback.message.edit_text(  # type: ignore
            "✍️ <b>Опишите ваш вопрос или проблему:</b>", parse_mode="HTML"
        )
        await state.set_state(SupportStates.waiting_for_question)
    elif callback.data == "profile_edit":
        skip_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Пропустить", callback_data="skip_username")]
            ]
        )
        await callback.message.edit_text(  # type: ignore
            "👤 <b>Пожалуйста, введите ваш username</b> (например, <code>@username</code>) или нажмите «Пропустить»:",
            reply_markup=skip_kb,
            parse_mode="HTML",
        )
        await state.set_state(SupportStates.waiting_for_username)


@support_router.callback_query(
    SupportStates.waiting_for_username, F.data == "skip_username"
)
async def skip_username(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(username="не указан")
    await callback.message.edit_text(  # type: ignore
        "📱 <b>Теперь введите ваш номер телефона</b> (например, <code>+79001234567</code>):",
        parse_mode="HTML",
    )
    await state.set_state(SupportStates.waiting_for_phone)


@support_router.message(SupportStates.waiting_for_username, F.text)
async def get_support_username(message: types.Message, state: FSMContext):
    username = message.text.strip()  # type: ignore
    if username.lower() in {"-", "пропустить"}:
        username = "не указан"
    elif not username.startswith("@") or len(username) < 3:
        await message.answer(
            "⚠️ <b>Пожалуйста, введите корректный username</b>, начинающийся с <code>@</code>, или нажмите «Пропустить».",
            parse_mode="HTML",
        )
        return
    await state.update_data(username=username)
    await message.answer(
        "📱 <b>Теперь введите ваш номер телефона</b> (например, <code>+79001234567</code>):",
        parse_mode="HTML",
    )
    await state.set_state(SupportStates.waiting_for_phone)


@support_router.message(SupportStates.waiting_for_phone, F.text)
async def get_support_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()  # type: ignore
    if not is_valid_phone(phone):
        await message.answer(
            "⚠️ <b>Пожалуйста, введите корректный номер телефона</b> в формате <code>+79001234567</code>.",
            parse_mode="HTML",
        )
        return
    await state.update_data(phone=phone)
    await message.answer("✍️ <b>Опишите ваш вопрос или проблему:</b>", parse_mode="HTML")
    await state.set_state(SupportStates.waiting_for_question)


@support_router.message(SupportStates.waiting_for_question, F.text)
async def get_support_question(message: types.Message, state: FSMContext):
    question = message.text.strip()  # type: ignore
    if not question:
        await message.answer(
            "❗️ <b>Пожалуйста, опишите ваш вопрос или проблему.</b>", parse_mode="HTML"
        )
        return

    data = await state.get_data()
    username = data.get("username")
    phone = data.get("phone")

    support_msg = (
        f"🆘 <b>Новое обращение в поддержку!</b>\n"
        f"👤 Username: <code>{username}</code>\n"
        f"📞 Телефон: <code>{phone}</code>\n"
        f"🆔 <a href='tg://user?id={message.from_user.id}'>Связаться с клиентом</a>\n\n"  # type: ignore
        f"❓ Вопрос:\n{question}"
    )
    await message.bot.send_message(  # type: ignore
        all_settings.different.support_group_id, support_msg, parse_mode="HTML"
    )
    await message.answer(
        "✅ <b>Ваше обращение отправлено в поддержку.</b>\n"
        "⏳ Мы свяжемся с вами в ближайшее время!",
        parse_mode="HTML",
    )
    await state.clear()
