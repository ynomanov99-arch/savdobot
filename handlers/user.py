"""
Klient handlerlari moduli.
/start, /help, /catalog, color raqam qidiruv,
sevimlilar va oxirgi ko'rilganlar handlerlari.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from config import (
    START_MESSAGE, HELP_MESSAGE, NOT_FOUND_MESSAGE,
    COSTUME_INFO_TEMPLATE, ADMIN_CONTACT, RECENT_LIMIT, CHANNEL_ID
)
from database import Database
from utils.color_parser import normalize_color_code, is_color_query
from keyboards.inline import get_costume_buttons, get_catalog_page_keyboard, get_variants_keyboard
from keyboards.reply import get_main_menu

logger = logging.getLogger(__name__)

router = Router(name="user")

CATALOG_PAGE_SIZE = 20


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database, state: FSMContext):
    await state.clear()
    await db.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or ""
    )
    await message.answer(
        START_MESSAGE.format(contact=ADMIN_CONTACT),
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@router.message(Command("help"))
@router.message(F.text == "❓ Yordam")
async def cmd_help(message: Message):
    await message.answer(
        HELP_MESSAGE.format(contact=ADMIN_CONTACT),
        parse_mode="HTML"
    )


@router.message(Command("catalog"))
@router.message(F.text == "📋 Katalog")
async def cmd_catalog(message: Message, db: Database):
    colors = await db.get_available_color_codes()
    if not colors:
        await message.answer("📋 Hozircha hech qanday kostum mavjud emas.", parse_mode="HTML")
        return
    total_pages = (len(colors) + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE
    await _send_catalog_page(message, colors, page=0, total_pages=total_pages)


async def _send_catalog_page(message: Message, colors: list, page: int, total_pages: int):
    start = page * CATALOG_PAGE_SIZE
    end = start + CATALOG_PAGE_SIZE
    page_colors = colors[start:end]
    text = "📋 <b>Mavjud kostyumlar:</b>\n\n"
    for i, (code, name) in enumerate(page_colors, start=start + 1):
        text += f"  {i}. <code>{code}</code> — {name}\n"
    text += f"\n📌 Color raqamini yuboring va ma'lumot oling!"
    text += f"\n\n📄 Sahifa {page + 1}/{total_pages}"
    keyboard = get_catalog_page_keyboard(page, total_pages)
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("catalog:"))
async def callback_catalog_page(callback: CallbackQuery, db: Database):
    page = int(callback.data.split(":")[1])
    colors = await db.get_available_color_codes()
    if not colors:
        await callback.answer("Hozircha kostumlar mavjud emas.", show_alert=True)
        return
    total_pages = (len(colors) + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE
    start = page * CATALOG_PAGE_SIZE
    end = start + CATALOG_PAGE_SIZE
    page_colors = colors[start:end]
    text = "📋 <b>Mavjud kostyumlar:</b>\n\n"
    for i, (code, name) in enumerate(page_colors, start=start + 1):
        text += f"  {i}. <code>{code}</code> — {name}\n"
    text += f"\n📌 Color raqamini yuboring va ma'lumot oling!"
    text += f"\n\n📄 Sahifa {page + 1}/{total_pages}"
    keyboard = get_catalog_page_keyboard(page, total_pages)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        pass
    await callback.answer()


@router.message(Command("favorites"))
@router.message(F.text == "❤️ Sevimlilar")
async def cmd_favorites(message: Message, db: Database):
    user_id = await db.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or ""
    )
    favorites = await db.get_favorites(user_id)
    if not favorites:
        await message.answer(
            "❤️ <b>Sevimlilar ro'yxati bo'sh.</b>\n\nKostum ma'lumotlarida ❤️ tugmasini bosib, sevimlilarga qo'shing!",
            parse_mode="HTML"
        )
        return
    text = "❤️ <b>Sevimli kostyumlaringiz:</b>\n\n"
    for costume in favorites:
        text += f"🎨 <code>{costume['color_code']}</code> — <b>{costume['name']}</b> | {costume['price']}\n"
    text += "\n📌 Ko'rish uchun color raqamini yuboring!"
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("fav:"))
async def callback_add_favorite(callback: CallbackQuery, db: Database):
    costume_id = int(callback.data.split(":", 1)[1])
    user_id = await db.register_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or ""
    )
    costume = await db.get_costume_by_id(costume_id)
    if not costume:
        await callback.answer("Kostum topilmadi!", show_alert=True)
        return
    success = await db.add_favorite(user_id, costume["id"])
    if success:
        await callback.answer("❤️ Sevimlilarga qo'shildi!", show_alert=True)
        keyboard = get_costume_buttons(costume["id"], is_favorite=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception:
            pass
    else:
        await callback.answer("Allaqachon sevimlilarda!", show_alert=True)


@router.callback_query(F.data.startswith("unfav:"))
async def callback_remove_favorite(callback: CallbackQuery, db: Database):
    costume_id = int(callback.data.split(":", 1)[1])
    user_id = await db.register_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or ""
    )
    costume = await db.get_costume_by_id(costume_id)
    if not costume:
        await callback.answer("Kostum topilmadi!", show_alert=True)
        return
    await db.remove_favorite(user_id, costume["id"])
    await callback.answer("💔 Sevimlilardan o'chirildi!", show_alert=True)
    keyboard = get_costume_buttons(costume["id"], is_favorite=False)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass


@router.message(Command("recent"))
@router.message(F.text == "🕐 Oxirgi ko'rilganlar")
async def cmd_recent(message: Message, db: Database):
    user_id = await db.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or ""
    )
    recent = await db.get_recent_searches(user_id, RECENT_LIMIT)
    if not recent:
        await message.answer(
            "🕐 <b>Hali hech narsa ko'rilmagan.</b>\n\nColor raqamini yuboring va kostyumlarni ko'ring!",
            parse_mode="HTML"
        )
        return
    text = "🕐 <b>Oxirgi ko'rilgan kostyumlar:</b>\n\n"
    for item in recent:
        text += f"🎨 <code>{item['color_code']}</code> — <b>{item['name']}</b> | {item['price']}\n"
    text += "\n📌 Qaytadan ko'rish uchun color raqamini yuboring!"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text)
async def search_costume(message: Message, db: Database, state: FSMContext):
    text = message.text.strip()
    if text.startswith('/'):
        return
    if not is_color_query(text):
        return
    color_code = normalize_color_code(text)
    if not color_code:
        return
    user_id = await db.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or ""
    )
    costumes = await db.get_costumes(color_code)
    if costumes:
        logger.info(f"Costume found: {color_code} for user {message.from_user.id}")
        await db.log_search(user_id, text, color_code, found=True)
        if len(costumes) == 1:
            await _send_costume_info(message, costumes[0], db, user_id)
        else:
            text_resp = f"🎨 <b>{color_code}</b> raqamli bir nechta kostyum topildi!\n\nIltimos, qaysi birini ko'rishni xohlasangiz tanlang:"
            await message.answer(text_resp, parse_mode="HTML", reply_markup=get_variants_keyboard(costumes))
    else:
        logger.info(f"Costume NOT found: {color_code} for user {message.from_user.id}")
        await db.log_search(user_id, text, color_code, found=False)
        await message.answer(
            NOT_FOUND_MESSAGE.format(contact=ADMIN_CONTACT),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("view_variant:"))
async def callback_view_variant(callback: CallbackQuery, db: Database):
    costume_id = int(callback.data.split(":")[1])
    user_id = await db.register_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or ""
    )
    costume = await db.get_costume_by_id(costume_id)
    if costume:
        await _send_costume_info(callback.message, costume, db, user_id)
    else:
        await callback.answer("Kostum topilmadi!", show_alert=True)
    await callback.answer()


async def _send_costume_info(message: Message, costume: dict, db: Database, user_id: int):
    # 1. Rasmlarni jo'natish (Maneken)
    mannequin_photos = costume.get("mannequin_photos", [])
    if mannequin_photos:
        try:
            if mannequin_photos and isinstance(mannequin_photos[0], int):
                # Import qilingan xabarlar (int message_id)
                await message.bot.copy_messages(
                    chat_id=message.chat.id,
                    from_chat_id=CHANNEL_ID,
                    message_ids=mannequin_photos,
                    remove_caption=True
                )
            else:
                # Qo'lda qo'shilgan rasmlar (string file_id)
                media_group = []
                for i, photo_id in enumerate(mannequin_photos):
                    caption = "📸 <b>Maneken ko'rinishi</b>" if i == 0 else None
                    media_group.append(InputMediaPhoto(media=photo_id, caption=caption, parse_mode="HTML"))
                await message.answer_media_group(media=media_group)
        except Exception as e:
            logger.error(f"Error sending mannequin photos: {e}")

    # 2. Rasmlarni jo'natish (Model)
    model_photos = costume.get("model_photos", [])
    if model_photos:
        try:
            media_group = []
            for i, photo_id in enumerate(model_photos):
                caption = "🧍 <b>Model ko'rinishi</b>" if i == 0 else None
                media_group.append(InputMediaPhoto(media=photo_id, caption=caption, parse_mode="HTML"))
            await message.answer_media_group(media=media_group)
        except Exception as e:
            logger.error(f"Error sending model photos: {e}")

    # 3. Matnni va klaviaturani jo'natish
    drop_val = costume.get("extra_note", "").strip() or "Ko'rsatilmagan"

    # Troyka yoki Dvoyka ekanligini aniqlash
    desc = costume.get("color_description", "").upper()
    name_upper = costume.get("name", "").upper()
    
    if "TROYKA" in desc or "TROYKA" in name_upper or "ТРОЙКА" in desc or "ТРОЙКА" in name_upper:
        suit_type = "TROYKS"
    elif "DVOYKA" in desc or "DVOYKA" in name_upper or "ДВОЙКА" in desc or "ДВОЙКА" in name_upper:
        suit_type = "DVOYKA"
    else:
        suit_type = "DVOYKA / TROYKS"

    stock_qty_val = costume.get("stock_qty", "Yo'q").strip() or "Yo'q"
    if stock_qty_val.isdigit():
        stock_qty_val = f"{stock_qty_val} ta"
        
    warehouse_location_val = costume.get("warehouse_location", "Ko'rsatilmagan").strip() or "Ko'rsatilmagan"

    sizes_formatted = " | ".join(s.strip() for s in costume["sizes"].split(","))

    info_text = COSTUME_INFO_TEMPLATE.format(
        color_code=costume["color_code"],
        name=costume["name"],
        sizes=sizes_formatted,
        drop=drop_val,
        suit_type=suit_type,
        stock_qty=stock_qty_val,
        warehouse_location=warehouse_location_val
    )

    is_fav = await db.is_favorite(user_id, costume["id"])
    keyboard = get_costume_buttons(costume["id"], is_favorite=is_fav)
    
    await message.answer(info_text, parse_mode="HTML", reply_markup=keyboard)


