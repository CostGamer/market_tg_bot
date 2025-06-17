from aiogram.fsm.state import State, StatesGroup


class AddressStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_address = State()
    waiting_for_index = State()
    waiting_for_name = State()
    waiting_for_edit_address = State()
    waiting_for_edit_field = State()
