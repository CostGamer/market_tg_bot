from aiogram import Router, types
from aiogram.filters import Command
from app.configs import all_settings

admin_media_router = Router()


@admin_media_router.message(Command("upload_video"))
async def request_video_upload(message: types.Message):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        await message.answer("Нет доступа.")
        return

    await message.answer(
        "📹 <b>Загрузка видео</b>\n\n"
        "Отправьте видео файл для получения file_id.\n"
        "После загрузки я пришлю вам file_id для использования в коде.",
        parse_mode="HTML",
    )


@admin_media_router.message(lambda message: message.content_type == "video")
async def handle_video_upload(message: types.Message):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        return

    video = message.video

    if video:
        file_info = (
            "📹 <b>Видео успешно загружено!</b>\n\n"
            f"<code>file_id: {video.file_id}</code>\n\n"
            f"📊 <b>Информация о файле:</b>\n"
            f"• Размер: {video.file_size / (1024*1024):.2f} MB\n"
            f"• Длительность: {video.duration} сек\n"
            f"• Разрешение: {video.width}x{video.height}\n\n"
            "💡 <b>Использование в коде:</b>\n"
            '<code>await message.answer_video(video="' + video.file_id + '")</code>'
        )

        await message.answer(file_info, parse_mode="HTML")
    else:
        await message.answer("❌ Ошибка при обработке видео")


@admin_media_router.message(Command("upload_photo"))
async def request_photo_upload(message: types.Message):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        await message.answer("Нет доступа.")
        return

    await message.answer(
        "📸 <b>Загрузка фото</b>\n\n" "Отправьте фото для получения file_id.",
        parse_mode="HTML",
    )


@admin_media_router.message(lambda message: message.content_type == "photo")
async def handle_photo_upload(message: types.Message):
    if message.from_user.id not in all_settings.different.list_of_admin_ids:  # type: ignore
        return

    photo = message.photo[-1]  # type: ignore

    file_info = (
        "📸 <b>Фото успешно загружено!</b>\n\n"
        f"<code>file_id: {photo.file_id}</code>\n\n"
        f"📊 <b>Информация о файле:</b>\n"
        f"• Размер: {photo.file_size / (1024*1024):.2f} MB\n"
        f"• Разрешение: {photo.width}x{photo.height}\n\n"
        "💡 <b>Использование в коде:</b>\n"
        '<code>await message.answer_photo(photo="' + photo.file_id + '")</code>'
    )

    await message.answer(file_info, parse_mode="HTML")
