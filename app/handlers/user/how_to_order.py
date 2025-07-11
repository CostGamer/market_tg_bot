from aiogram import Router, types
from aiogram.filters import Command
from app.configs import all_settings

how_to_order_router = Router()


@how_to_order_router.message(Command("how_to_order"))
async def how_to_order_handler(message: types.Message):
    caption_text = (
        "📹 <b>Как сделать заказ - пошаговая инструкция</b>\n\n"
        "В этом видео вы узнаете:\n"
        "• Как найти товар на китайских сайтах\n"
        "• Как правильно оформить заказ\n"
        "🚀 <b>Сделай свой первый заказ /order !!!</b>\n\n"
        "❓ Остались вопросы? Обратитесь в поддержку /support"
    )

    await message.answer_video(
        video=all_settings.different.video_order_id,
        caption=caption_text,
        parse_mode="HTML",
    )
