from aiogram.fsm.state import State, StatesGroup


class AddressStates(StatesGroup):
    choosing_address = State()
    manage_address = State()
    edit_field_choice = State()
    waiting_for_edit_field = State()

    waiting_for_city = State()
    waiting_for_address = State()
    waiting_for_index = State()
    waiting_for_name = State()
