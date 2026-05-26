"""
Reply tugmalar moduli.
Asosiy menyu va boshqa reply keyboard tugmalari.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_menu() -> ReplyKeyboardMarkup:
    """Asosiy menyu (klient uchun)."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Katalog"),
                KeyboardButton(text="❤️ Sevimlilar"),
            ],
            [
                KeyboardButton(text="🕐 Oxirgi ko'rilganlar"),
                KeyboardButton(text="❓ Yordam"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Color raqamini yuboring..."
    )
    return keyboard


def get_admin_reply_menu() -> ReplyKeyboardMarkup:
    """Admin uchun reply keyboard."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Qo'shish"),
                KeyboardButton(text="📋 Ro'yxat"),
            ],
            [
                KeyboardButton(text="📊 Statistika"),
                KeyboardButton(text="📢 Broadcast"),
            ],
            [
                KeyboardButton(text="🔙 Oddiy menyu"),
            ],
        ],
        resize_keyboard=True,
    )
    return keyboard


def remove_keyboard() -> ReplyKeyboardRemove:
    """Keyboard ni olib tashlash."""
    return ReplyKeyboardRemove()
