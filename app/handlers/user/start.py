import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.keyboards import get_start_keyboard

logger = logging.getLogger(__name__)
start_router = Router()


@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "🇨🇳 Я помогу вам заказать товары из Китая быстро и удобно!\n\n"
        "🔧 <b>Что я умею:</b>\n"
        "• Оформление заказов с расчетом стоимости\n"
        "• Управление профилем и адресами доставки\n"
        "• Отслеживание статуса ваших заказов\n"
        "• Проверка курса валют и расчет цен\n"
        "• Связь с поддержкой\n\n"
        "📱 <b>Выберите действие:</b>"
    )

    await message.answer(
        welcome_text, reply_markup=get_start_keyboard(), parse_mode="HTML"
    )


@start_router.message(
    lambda message: message.text
    in [
        "👤 Профиль",
        "📋 Оформить заказ",
        "📍 Адреса",
        "📦 Мои заказы",
        "💱 Курс валют",
        "🧮 Калькулятор",
        "💬 Поддержка",
    ]
)
async def handle_keyboard_buttons(message: types.Message, state: FSMContext):
    """Обработчик нажатий на кнопки клавиатуры"""

    try:
        if message.text == "👤 Профиль":
            from .profile import show_profile

            await show_profile(message)

        elif message.text == "📋 Оформить заказ":
            from .order import start_order

            await start_order(message, state)

        elif message.text == "📍 Адреса":
            from .addresses import show_addresses_command

            await show_addresses_command(message, state)

        elif message.text == "📦 Мои заказы":
            from .order_history import show_user_orders

            await show_user_orders(message)

        elif message.text == "💱 Курс валют":
            from .current_rate import show_current_rate

            await show_current_rate(message)

        elif message.text == "🧮 Калькулятор":
            from .price_calc import start_calc

            await start_calc(message, state)

        elif message.text == "💬 Поддержка":
            from .support import start_support

            await start_support(message, state)

    except ImportError as e:
        logger.error(f"Не удалось импортировать обработчик: {e}")
        await message.answer("❌ Команда временно недоступна")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды {message.text}: {e}")
        await message.answer("❌ Произошла ошибка при выполнении команды")
