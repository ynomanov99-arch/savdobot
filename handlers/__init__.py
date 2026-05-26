"""
Handlerlar paketi.
Barcha routerlarni ro'yxatdan o'tkazish.
"""

from aiogram import Router

from handlers.admin import router as admin_router
from handlers.user import router as user_router
from handlers.common import router as common_router
from handlers.channel import router as channel_router


def get_all_routers() -> list[Router]:
    """
    Barcha routerlarni tartib bilan qaytaradi.
    MUHIM: Tartib muhim! Admin va common routerlar
    user routerdan OLDIN ro'yxatga olinishi kerak,
    chunki user router barcha matnli xabarlarni ushlaydi.
    """
    return [
        channel_router,  # Avtomatik kanaldan import qilish handleri
        common_router,   # Umumiy (cancel, start callback)
        admin_router,    # Admin (buyruqlar + FSM)
        user_router,     # Klient (qidiruv - eng oxirida)
    ]
