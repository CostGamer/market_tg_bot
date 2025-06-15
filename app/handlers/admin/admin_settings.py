from aiogram import Router, types
from aiogram.filters import Command
from app.models.pydantic_models import AdminSettingsPM
from app.repositories import AdminSettingsRepo
from app.configs import db_connection
from app.configs import all_settings

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
            f"Текущие параметры:\n"
            f"Комиссия: {settings.commision_rate}\n"
            f"Доставка за кг: {settings.kilo_delivery}\n"
            f"Наценка CNY: {settings.cny_rate_syrcharge}\n"
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
