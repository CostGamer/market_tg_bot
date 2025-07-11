import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.keyboards import get_start_keyboard
from app.repositories import UserRepo
from app.configs import db_connection

logger = logging.getLogger(__name__)
start_router = Router()


@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
    async with db_connection.get_session() as session:
        try:
            user_repo = UserRepo(session)
            user_tg_id = message.from_user.id  # type: ignore
            tg_username = message.from_user.username  # type: ignore

            existing_user = await user_repo.get_user_info(user_tg_id)

            if not existing_user:
                await user_repo.create_user_with_tg_id(user_tg_id, tg_username)
                logger.info(f"Создан новый пользователь с tg_id: {user_tg_id}")
            else:
                if existing_user.tg_username != tg_username:
                    await user_repo.update_username(user_tg_id, tg_username)
                    logger.info(f"Обновлен username для пользователя {user_tg_id}")

            await session.commit()

        except Exception as e:
            logger.error(
                f"Ошибка при сохранении пользователя {message.from_user.id}: {e}"
            )
            await session.rollback()

    welcome_text = (
        "👋 <b>Добро пожаловать в ChinaEasyBot!</b>\n\n"
        "🇨🇳 Здесь вы легко и быстро закажете любые товары из Китая — без хлопот и лишних вопросов.\n\n"
        "✨ <b>Возможности бота:</b>\n"
        "• 📦 Мгновенное оформление и расчет стоимости заказа\n"
        "• 🏠 Удобное управление профилем и адресами доставки\n"
        "• 🚚 Онлайн-отслеживание ваших посылок\n"
        "• 💱 Актуальный курс валют и автоматический расчет цен\n"
        "• 🛎️ Оперативная поддержка!\n\n"
        "👇 <b>Выберите нужную функцию и начните свой заказ!</b>"
    )

    await message.answer(
        welcome_text, reply_markup=get_start_keyboard(), parse_mode="HTML"
    )


@start_router.message(
    lambda message: message.text
    in [
        "🤔 Как заказать?",
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
    try:
        if message.text == "👤 Профиль":
            from .profile import show_profile

            await show_profile(message)
        elif message.text == "🤔 Как заказать?":
            from .how_to_order import how_to_order_handler

            await how_to_order_handler(message)
        elif message.text == "📋 Оформить заказ":
            from .order import start_order

            await start_order(message, state)
        elif message.text == "📍 Адреса":
            from . import addresses

            await addresses.show_addresses_command(message, state)
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
