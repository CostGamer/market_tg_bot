from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from app.services import PriceCalculator
from app.states import CalcOrderStates
from app.repositories import AdminSettingsRepo
from app.configs import db_connection
from app.keyboards.categories import (
    get_main_categories_keyboard,
    get_subcategories_keyboard,
)
from app.configs.mappers import KILO_MAPPER, SUBCATEGORY_NAMES, MAIN_CATEGORY_NAMES

price_calc_router = Router()


@price_calc_router.message(Command("calculate_price"))
async def start_calc(message: types.Message, state: FSMContext):
    await message.answer("Введите стоимость товара в юанях 🇨🇳!")
    await state.set_state(CalcOrderStates.waiting_for_price)


@price_calc_router.message(CalcOrderStates.waiting_for_price, F.text)
async def get_price(message: types.Message, state: FSMContext):
    text = message.text.replace(",", ".").strip()  # type: ignore
    try:
        price = float(text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректную положительную сумму.")
        return

    await state.update_data(price=price)
    await message.answer(
        "Выберите категорию 📂:",
        reply_markup=get_main_categories_keyboard(),
    )
    await state.set_state(CalcOrderStates.waiting_for_main_category)


@price_calc_router.callback_query(
    CalcOrderStates.waiting_for_main_category, F.data.startswith("maincat_")
)
async def main_category_selected(callback: types.CallbackQuery, state: FSMContext):
    main_cat_id = callback.data[len("maincat_") :]  # type: ignore
    await state.update_data(main_cat_id=main_cat_id)
    subcats = KILO_MAPPER[main_cat_id]
    if isinstance(subcats, int):
        await finish_calc(callback, state, main_cat_id, None)
    else:
        await callback.message.edit_reply_markup(reply_markup=get_subcategories_keyboard(main_cat_id))  # type: ignore
        await callback.answer()
        await state.set_state(CalcOrderStates.waiting_for_subcategory)


@price_calc_router.callback_query(
    CalcOrderStates.waiting_for_subcategory, F.data.startswith("subcat_")
)
async def subcategory_selected(callback: types.CallbackQuery, state: FSMContext):
    _, main_cat_id, sub_id = callback.data.split("_", 2)  # type: ignore
    await finish_calc(callback, state, main_cat_id, sub_id)


async def finish_calc(callback, state, main_cat_id, sub_id):
    data = await state.get_data()
    price = data["price"]
    if sub_id:
        cat_str = f"{MAIN_CATEGORY_NAMES[main_cat_id]} / {SUBCATEGORY_NAMES[main_cat_id][sub_id]}"
    else:
        cat_str = MAIN_CATEGORY_NAMES[main_cat_id]

    async with db_connection.get_session() as session:
        admin_settings_repo = AdminSettingsRepo(session)
        calc = PriceCalculator(price, admin_settings_repo)
        total, fee = await calc.calculate_price(
            price, category=main_cat_id, subcategory=sub_id
        )

    fee_str = f"{fee:.2f}" if fee is not None else "нет"

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"Категория 📂: {cat_str}\n"
        f"Стоимость в юанях 🇨🇳: {price:.2f}\n"
        f"Пошлина 🛃: {fee_str}\n"
        f"Итого к оплате 🇷🇺: {total:.2f} руб."
    )
    await state.clear()
    await callback.answer()


@price_calc_router.callback_query(
    CalcOrderStates.waiting_for_subcategory, F.data == "back_to_main_categories"
)
async def back_to_main_categories(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=get_main_categories_keyboard())  # type: ignore
    await state.set_state(CalcOrderStates.waiting_for_main_category)
    await callback.answer()
