from aiogram.fsm.state import StatesGroup, State


class AdminFAQStates(StatesGroup):
    waiting_for_faq = State()
