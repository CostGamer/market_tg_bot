from aiogram import Router
from .price_calc import price_calc_router
from .current_rate import current_rate_router


user_router = Router()
user_router.include_router(price_calc_router)
user_router.include_router(current_rate_router)
