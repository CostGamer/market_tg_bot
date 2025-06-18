from aiogram import Router, types
from aiogram.filters import Command
from app.services import CurrentRate
from app.repositories import AdminSettingsRepo
from app.configs import db_connection

current_rate_router = Router()


@current_rate_router.message(Command("current_rate"))
async def show_current_rate(message: types.Message):
    async with db_connection.get_session() as session:
        admin_settings_repo = AdminSettingsRepo(session)
        current_rate_service = CurrentRate(admin_settings_repo)
        cny_rate = await current_rate_service.current_rate()

    await message.answer(
        f"Текущий курс юаня: <b>{cny_rate:.2f}</b> руб.", parse_mode="HTML"
    )
