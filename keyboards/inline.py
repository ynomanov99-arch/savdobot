"""
Inline tugmalar moduli.
Klient va admin uchun inline keyboard tugmalari.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_CONTACT


def get_costume_buttons(costume_id: int, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """
    Kostum ma'lumotlari ostida ko'rsatiladigan tugmalar.
    Barcha tugmalar (Buyurtma berish, Sevimlilar, Bosh sahifa) olib tashlanganligi sababli None qaytaradi.
    """
    return None


def get_admin_menu() -> InlineKeyboardMarkup:
    """Admin panel menyusi tugmalari."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="➕ Kostum qo'shish", callback_data="admin:add"),
        InlineKeyboardButton(text="📋 Ro'yxat", callback_data="admin:list"),
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="admin:edit"),
        InlineKeyboardButton(text="🗑 O'chirish", callback_data="admin:delete"),
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Aktiv/Nofaol", callback_data="admin:toggle"),
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin:stats"),
    )
    builder.row(
        InlineKeyboardButton(text="📢 Broadcast", callback_data="admin:broadcast"),
        InlineKeyboardButton(text="📥 Excel eksport", callback_data="admin:export"),
    )

    return builder.as_markup()


def get_edit_fields_keyboard(costume_id: int) -> InlineKeyboardMarkup:
    """Tahrirlash uchun maydonlar ro'yxati."""
    builder = InlineKeyboardBuilder()

    fields = [
        ("👔 Nomi", "edit_field:name"),
        ("💰 Narxi", "edit_field:price"),
        ("📏 O'lchamlar", "edit_field:sizes"),
        ("🧵 Material", "edit_field:material"),
        ("🎨 Rang tavsifi", "edit_field:color_description"),
        ("📸 Maneken rasmlari", "edit_field:mannequin_photos"),
        ("🧍 Model rasmlari", "edit_field:model_photos"),
        ("📝 Qo'shimcha izoh", "edit_field:extra_note"),
    ]

    for text, callback in fields:
        builder.row(InlineKeyboardButton(text=text, callback_data=f"{callback}:{costume_id}"))

    builder.row(
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:cancel")
    )

    return builder.as_markup()


def get_confirm_keyboard(action: str, costume_id: int) -> InlineKeyboardMarkup:
    """Tasdiqlash tugmalari (o'chirish, broadcast uchun)."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Ha, tasdiqlash",
            callback_data=f"confirm:{action}:{costume_id}"
        ),
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="admin:cancel"
        ),
    )

    return builder.as_markup()


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Broadcast tasdiqlash tugmalari."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✅ Ha, barchaga yuborish", callback_data="broadcast:confirm"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:cancel"),
    )

    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Bekor qilish tugmasi (FSM jarayonlari uchun)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:cancel")
    )
    return builder.as_markup()


def get_notify_keyboard() -> InlineKeyboardMarkup:
    """Yangi kostum qo'shilganda — foydalanuvchilarga xabar yuborish tugmalari."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📢 Ha, barchaga xabar berish",
            callback_data="notify:yes"
        ),
        InlineKeyboardButton(
            text="🚫 Yo'q",
            callback_data="notify:no"
        ),
    )
    return builder.as_markup()


def get_catalog_page_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Catalog sahifalash tugmalari."""
    builder = InlineKeyboardBuilder()

    buttons = []
    if page > 0:
        buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"catalog:{page - 1}")
        )
    if page < total_pages - 1:
        buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"catalog:{page + 1}")
        )

    if buttons:
        builder.row(*buttons)

    return builder.as_markup()


def get_variants_keyboard(costumes: list, prefix: str = "view_variant") -> InlineKeyboardMarkup:
    """Bir nechta variant topilganda tanlash tugmalari."""
    builder = InlineKeyboardBuilder()
    
    for c in costumes:
        name = c.get("name", "Noma'lum")
        price = c.get("price", "")
        btn_text = f"👔 {name} - {price}" if price and price != "Narx ko'rsatilmagan" else f"👔 {name}"
        builder.row(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"{prefix}:{c['id']}"
            )
        )
        
    builder.row(
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="start" if prefix == "view_variant" else "admin:cancel"
        )
    )
    
    return builder.as_markup()
