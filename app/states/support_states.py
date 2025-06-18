from aiogram.fsm.state import StatesGroup, State


class SupportStates(StatesGroup):
    waiting_for_faq_confirmation = State()
    waiting_for_username = State()
    waiting_for_phone = State()
    waiting_for_question = State()
