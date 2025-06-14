from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.services import PriceCalculator
from app.states import CalcOrderStates
from app.keyboards.categories import get_categories_inline_keyboard
from aiogram.filters import Command

price_calc_router = Router()


@price_calc_router.message(Command("calculate_price"))
async def start_calc(message: types.Message, state: FSMContext):
    await message.answer("Введите стоимость товара в юанях!")
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
        "Выберите категорию товара:",
        reply_markup=get_categories_inline_keyboard(page=0),
    )
    await state.set_state(CalcOrderStates.waiting_for_category)


@price_calc_router.callback_query(F.data.startswith("cat_page_"))
async def paginate_categories(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[-1])  # type: ignore
    await callback.message.edit_reply_markup(  # type: ignore
        reply_markup=get_categories_inline_keyboard(page=page)
    )
    await callback.answer()


@price_calc_router.callback_query(
    CalcOrderStates.waiting_for_category, F.data.startswith("cat_")
)
async def category_selected(callback: types.CallbackQuery, state: FSMContext):
    if callback.data.startswith("cat_page_"):  # type: ignore
        await callback.answer()
        return

    category = callback.data[4:]  # type: ignore
    data = await state.get_data()
    price = data["price"]

    calc = PriceCalculator(price)
    total, fee = await calc.calculate_price(price, category=category)

    fee_str = f"{fee:.2f}" if fee is not None else "нет"

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore

    await callback.message.answer(  # type: ignore
        f"Категория: {category}\n"
        f"Стоимость в юанях: {price:.2f}\n"
        f"Пошлина: {fee_str}\n"
        f"Итого к оплате: {total:.2f}"
    )
    await state.clear()
    await callback.answer()
