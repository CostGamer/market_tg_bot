from aiogram import Router
from .price_calc import price_calc_router
from .current_rate import current_rate_router
from .profile import profile_router
from .addresses import addresses_router
from .support import support_router
from .order import order_router


user_router = Router()
user_router.include_router(price_calc_router)
user_router.include_router(current_rate_router)
user_router.include_router(profile_router)
user_router.include_router(support_router)
user_router.include_router(order_router)
user_router.include_router(addresses_router)
