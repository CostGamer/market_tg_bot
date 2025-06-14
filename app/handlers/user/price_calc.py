from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.services import PriceCalculator
from app.states import CalcOrderStates
from app.keyboards.categories import get_categories_keyboard
from aiogram.filters import Command

price_calc_router = Router()


@price_calc_router.message(Command("calculate_price"))
async def start_calc(message: types.Message, state: FSMContext):
    await message.answer("Введите стоимость товара в юанях!!!")
    await state.set_state(CalcOrderStates.waiting_for_price)


@price_calc_router.message(CalcOrderStates.waiting_for_price, F.text)
async def get_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))  # type: ignore
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректную положительную сумму.")
        return
    await state.update_data(price=price)
    await message.answer(
        "Выберите категорию товара:", reply_markup=get_categories_keyboard()
    )
    await state.set_state(CalcOrderStates.waiting_for_category)


@price_calc_router.message(CalcOrderStates.waiting_for_category, F.text)
async def get_category(message: types.Message, state: FSMContext):
    category = message.text.strip()  # type: ignore
    data = await state.get_data()
    price = data["price"]

    calc = PriceCalculator(price)
    total, fee = await calc.calculate_price(price, category=category)

    fee_str = f"{fee:.2f}" if fee is not None else "нет"

    await message.answer(
        f"Категория: {category}\n"
        f"Стоимость в юанях: {price:.2f}\n"
        f"Пошлина: {fee_str}\n"
        f"Итого к оплате: {total:.2f}",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.clear()
