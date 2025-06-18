from aiogram.fsm.state import StatesGroup, State


class CalcOrderStates(StatesGroup):
    waiting_for_price = State()
    waiting_for_main_category = State()
    waiting_for_subcategory = State()
