from aiogram.fsm.state import State, StatesGroup


class OrderAdminStates(StatesGroup):
    waiting_china_track = State()
    waiting_russia_track = State()
    waiting_qr_code = State()
