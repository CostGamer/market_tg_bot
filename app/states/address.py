from aiogram.fsm.state import State, StatesGroup


class AddressStates(StatesGroup):
    choosing_address = State()
    manage_address = State()
    waiting_for_city = State()
    confirm_city = State()
    waiting_for_address = State()
    confirm_address = State()
    waiting_for_index = State()
    confirm_index = State()
    waiting_for_name = State()
    confirm_name = State()
    final_confirmation = State()
