from aiogram import Router, types, F
from aiogram.filters import Command
from app.models.pydantic_models import AdminSettingsPM
from app.repositories import AdminSettingsRepo
from app.configs import db_connection
from aiogram.fsm.context import FSMContext
from app.configs import all_settings
from app.states import AdminFAQStates

admin_settings_router = Router()


@admin_settings_router.message(Command("admin_settings"))
async def show_admin_settings(message: types.Message):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        await message.answer("Нет доступа.")
        return

    async with db_connection.get_session() as session:
        repo = AdminSettingsRepo(session)
        settings = await repo.get_settings()
        if settings is None:
            await message.answer("Настройки не найдены.")
            return

        await message.answer(
            f"Текущие параметры:\n\n"
            f"Комиссия: {settings.commision_rate}\n\n"
            f"Доставка за кг: {settings.kilo_delivery}\n\n"
            f"Наценка CNY: {settings.cny_rate_syrcharge}\n\n"
            f"FAQ:\n{settings.faq}"
        )


@admin_settings_router.message(Command("set_admin_settings"))
async def set_admin_settings(message: types.Message):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        await message.answer("Нет доступа.")
        return

    parts = message.text.split()  # type: ignore
    if len(parts) != 5:
        await message.answer(
            "Формат: /set_admin_settings <комиссия> <доставка> <наценка> <стоимость проверки>"
        )
        return

    try:
        commision_rate = float(parts[1])
        kilo_delivery = float(parts[2])
        cny_rate_syrcharge = float(parts[3])
        additional_control = int(parts[4])
    except ValueError:
        await message.answer("Проверьте формат чисел.")
        return

    async with db_connection.get_session() as session:
        repo = AdminSettingsRepo(session)

        new_settings = AdminSettingsPM(
            commision_rate=commision_rate,
            kilo_delivery=kilo_delivery,
            cny_rate_syrcharge=cny_rate_syrcharge,
            additional_control=additional_control,
            user_tg_id=message.from_user.id,  # type: ignore
        )
        updated = await repo.update_settings(new_settings)
        await message.answer(
            f"Обновлено:\n"
            f"Комиссия: {updated.commision_rate}\n"
            f"Доставка за кг: {updated.kilo_delivery}\n"
            f"Наценка CNY: {updated.cny_rate_syrcharge}\n"
            f"Стоимость проверки: {updated.additional_control}"
        )


@admin_settings_router.message(Command("set_faq"))
async def start_set_faq(message: types.Message, state: FSMContext):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        await message.answer("Нет доступа.")
        return
    await message.answer("Введите новый текст FAQ:")
    await state.set_state(AdminFAQStates.waiting_for_faq)


@admin_settings_router.message(AdminFAQStates.waiting_for_faq, F.text)
async def process_new_faq(message: types.Message, state: FSMContext):
    new_faq = message.text.strip()  # type: ignore
    if not new_faq:
        await message.answer("FAQ не может быть пустым. Введите текст FAQ:")
        return

    async with db_connection.get_session() as session:
        repo = AdminSettingsRepo(session)
        updated = await repo.update_faq(new_faq)
        await message.answer(f"FAQ успешно обновлён!\n\n" f"Новый FAQ:\n{updated.faq}")
    await state.clear()
