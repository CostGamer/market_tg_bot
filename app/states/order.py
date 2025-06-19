from aiogram.fsm.state import StatesGroup, State


class OrderStates(StatesGroup):
    waiting_for_url = State()
    confirm_url = State()
    waiting_for_photo = State()
    waiting_for_price = State()
    confirm_price = State()
    waiting_for_quantity = State()
    waiting_for_description = State()
    confirm_description = State()
    choosing_address = State()
    waiting_for_address_city = State()
    waiting_for_address_address = State()
    waiting_for_address_index = State()
    waiting_for_address_name = State()
    waiting_for_phone = State()
    waiting_for_username = State()
    order_review = State()
    waiting_for_admin_comment = State()
