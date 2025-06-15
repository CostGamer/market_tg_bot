from aiogram import Router
from .admin_settings import admin_settings_router

admin_router = Router()
admin_router.include_router(admin_settings_router)
