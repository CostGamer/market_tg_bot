from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.repositories import OrderRepo
from app.configs import db_connection, all_settings
from app.states import OrderAdminStates
from app.keyboards import create_order_status_keyboard
from app.services.order_admin_service import OrderAdminService
from app.utils.order_formatter import format_order_info
from logging import getLogger

logger = getLogger(__name__)

order_admin_router = Router()


@order_admin_router.message(Command("order_status"))
async def show_order_status_menu(message: types.Message):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        await message.answer("Нет доступа.")
        return

    parts = message.text.split()  # type: ignore
    if len(parts) != 2:
        await message.answer(
            "❌ Неверный формат команды!\n"
            "Используйте: <code>/order_status &lt;номер_заказа&gt;</code>",
            parse_mode="HTML",
        )
        return

    try:
        order_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID заказа должен быть числом!")
        return

    async with db_connection.get_session() as session:
        repo = OrderRepo(session)
        order = await repo.get_order_with_user(order_id)

        if not order:
            await message.answer(f"❌ Заказ #{order_id} не найден!")
            return

        order_info = format_order_info(order)
        keyboard = create_order_status_keyboard(order_id)

        await message.answer(order_info, parse_mode="HTML", reply_markup=keyboard)


@order_admin_router.callback_query(F.data.startswith("order_status_"))
async def handle_order_status_callback(
    callback: types.CallbackQuery, state: FSMContext
):
    if callback.from_user.id not in all_settings.different.list_of_admin_ids:
        await callback.answer("Нет доступа!", show_alert=True)
        return

    try:
        parts = callback.data.split("_")  # type: ignore
        order_id = int(parts[2])
        action = parts[3]

        async with db_connection.get_session() as session:
            repo = OrderRepo(session)
            service = OrderAdminService(repo, callback.bot)

            order = await repo.get_order_with_user(order_id)
            if not order:
                await callback.answer("❌ Заказ не найден!", show_alert=True)
                return

            if action == "shipping":
                await state.update_data(order_id=order_id)
                await state.set_state(OrderAdminStates.waiting_china_track)
                await callback.message.reply(  # type: ignore
                    f"📦 Введите трек-номер для отправки в Китае (заказ #{order_id}):"
                )
                await callback.answer()
                return

            elif action == "delivering":
                await state.update_data(order_id=order_id)
                await state.set_state(OrderAdminStates.waiting_russia_track)
                await callback.message.reply(  # type: ignore
                    f"🚚 Введите трек-номер для доставки по России (заказ #{order_id}):"
                )
                await callback.answer()
                return

            elif action == "ready":
                await state.update_data(order_id=order_id)
                await state.set_state(OrderAdminStates.waiting_qr_code)
                await callback.message.reply(  # type: ignore
                    f"📍 Отправьте QR-код для получения заказа #{order_id}:"
                )
                await callback.answer()
                return

            result = await service.update_order_status_simple(order_id, action)

            if result:
                await callback.answer(f"✅ {result['message']}")

                updated_order = await repo.get_order_with_user(order_id)
                if updated_order:
                    order_info = format_order_info(updated_order)
                    keyboard = create_order_status_keyboard(order_id)

                    try:
                        await callback.message.edit_text(  # type: ignore
                            order_info, parse_mode="HTML", reply_markup=keyboard
                        )
                    except Exception as e:
                        logger.warning(f"Не удалось обновить сообщение: {e}")
            else:
                await callback.answer(
                    "❌ Ошибка при обновлении статуса!", show_alert=True
                )

    except Exception as e:
        logger.error(f"Ошибка в handle_order_status_callback: {e}")
        await callback.answer("❌ Произошла ошибка!", show_alert=True)


@order_admin_router.message(OrderAdminStates.waiting_china_track, F.text)
async def process_china_track(message: types.Message, state: FSMContext):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        await message.answer("Нет доступа.")
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    china_track = message.text.strip()  # type: ignore

    if not china_track:
        await message.reply("❌ Трек-номер не может быть пустым!")
        return

    async with db_connection.get_session() as session:
        repo = OrderRepo(session)
        service = OrderAdminService(repo, message.bot)
        result = await service.update_order_with_china_track(order_id, china_track)  # type: ignore

        if result:
            await message.reply(
                f"✅ Заказ #{order_id} переведен в статус 'Едет на склад'\n"
                f"🇨🇳 Трек-номер: <code>{china_track}</code>",
                parse_mode="HTML",
            )
        else:
            await message.reply("❌ Произошла ошибка при сохранении трек-номера!")

    await state.clear()


@order_admin_router.message(OrderAdminStates.waiting_russia_track, F.text)
async def process_russia_track(message: types.Message, state: FSMContext):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        await message.answer("Нет доступа.")
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    russia_track = message.text.strip()  # type: ignore

    if not russia_track:
        await message.reply("❌ Трек-номер не может быть пустым!")
        return

    async with db_connection.get_session() as session:
        repo = OrderRepo(session)
        service = OrderAdminService(repo, message.bot)
        result = await service.update_order_with_russia_track(order_id, russia_track)  # type: ignore

        if result:
            await message.reply(
                f"✅ Заказ #{order_id} переведен в статус 'Доставляется'\n"
                f"🇷🇺 Трек-номер: <code>{russia_track}</code>",
                parse_mode="HTML",
            )
        else:
            await message.reply("❌ Произошла ошибка при сохранении трек-номера!")

    await state.clear()


@order_admin_router.message(OrderAdminStates.waiting_qr_code, F.photo)
async def process_qr_code(message: types.Message, state: FSMContext):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        await message.answer("Нет доступа.")
        return

    data = await state.get_data()
    order_id = data.get("order_id")

    qr_photo = message.photo[-1].file_id  # type: ignore

    async with db_connection.get_session() as session:
        repo = OrderRepo(session)
        service = OrderAdminService(repo, message.bot)
        result = await service.update_order_to_ready_with_qr(order_id, qr_photo)  # type: ignore

        if result:
            await message.reply(
                f"✅ Заказ #{order_id} переведен в статус 'Ожидает получения'\n"
                f"📱 QR-код отправлен клиенту"
            )
        else:
            await message.reply("❌ Произошла ошибка при сохранении QR-кода!")

    await state.clear()


@order_admin_router.message(OrderAdminStates.waiting_qr_code)
async def qr_code_not_photo(message: types.Message, state: FSMContext):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        await message.answer("Нет доступа.")
        return

    await message.reply("❌ Пожалуйста, отправьте QR-код в виде фотографии!")
