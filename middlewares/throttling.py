"""
Throttling middleware — Flood himoyasi.
Har bir foydalanuvchi uchun 1 daqiqada maksimal so'rov sonini cheklaydi.
"""

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import RATE_LIMIT, RATE_LIMIT_PERIOD


class ThrottlingMiddleware(BaseMiddleware):
    """
    Flood himoyasi middleware.
    
    Har bir foydalanuvchi uchun so'rovlar sonini kuzatadi.
    Agar belgilangan vaqt oralig'ida ko'p so'rov yuborilsa,
    foydalanuvchiga ogohlantirish yuboradi va so'rovni rad etadi.
    """

    def __init__(self):
        super().__init__()
        # {user_id: [timestamp1, timestamp2, ...]}
        self.requests: Dict[int, list[float]] = {}

    def _clean_old_requests(self, user_id: int):
        """Eskirgan so'rovlarni tozalash."""
        if user_id not in self.requests:
            return

        current_time = time.time()
        self.requests[user_id] = [
            ts for ts in self.requests[user_id]
            if current_time - ts < RATE_LIMIT_PERIOD
        ]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Middleware asosiy funksiyasi."""

        # Faqat Message uchun ishlaydi
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        # Eskirgan so'rovlarni tozalash
        self._clean_old_requests(user_id)

        # So'rovlar sonini tekshirish
        if user_id in self.requests and len(self.requests[user_id]) >= RATE_LIMIT:
            # Cheklovga yetdi — ogohlantirish
            await event.answer(
                "⚠️ <b>Juda ko'p so'rov!</b>\n\n"
                f"Iltimos, {RATE_LIMIT_PERIOD} soniya kutib turing va qaytadan urinib ko'ring.",
                parse_mode="HTML"
            )
            return None

        # So'rovni ro'yxatga qo'shish
        if user_id not in self.requests:
            self.requests[user_id] = []
        self.requests[user_id].append(time.time())

        # Handleni davom ettirish
        return await handler(event, data)
