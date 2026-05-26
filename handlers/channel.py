"""
Telegram kanaldan yangi postlarni avtomat ushlab olib bazaga yozish handleri.
"""

import asyncio
import json
import logging
import re
from aiogram import Router
from aiogram.types import Message

from config import CHANNEL_ID
from database import Database
from utils.color_parser import normalize_color_code

logger = logging.getLogger(__name__)
router = Router()

# Guruhlangan rasmlar (album/media group) uchun cache va locklar
media_group_cache = {}
media_group_locks = {}


def parse_costume(text: str) -> dict | None:
    """Post matnidan kostum ma'lumotlarini ajratib olish."""
    if not text:
        return None

    data = {}

    # Model nomi (O'zbekcha / Ruscha formatlar)
    model = re.search(r"(Model|Модель)\s*[^a-zA-Z0-9\s]?\s*(.+)", text, re.IGNORECASE)
    if model:
        data["name"] = model.group(2).strip()

    # Color raqam
    color = re.search(r"(Color|Цвет)\s*[^a-zA-Z0-9\s]?\s*(.+)", text, re.IGNORECASE)
    if color:
        data["color_code"] = color.group(2).strip()

    # Drop
    drop = re.search(r"(Drop|Дроп)\s*[^a-zA-Z0-9\s]?\s*(.+)", text, re.IGNORECASE)
    if drop:
        data["drop"] = drop.group(2).strip()

    # Size
    size = re.search(r"(Size|Размер|Razmer)\s*[^a-zA-Z0-9\s]?\s*(.+)", text, re.IGNORECASE)
    if size:
        data["sizes"] = size.group(2).strip()

    # Tavsif (matnning eng oxirgi qatori)
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if lines:
        data["description"] = lines[-1]

    # Agar color_code topilmasa, bu kostyum posti emas
    if "color_code" not in data:
        return None

    return data


async def process_and_save_costume(text: str, mannequin_photos: list[int], db: Database):
    """Postni tahlil qilib, bazaga qo'shish yoki yangilash."""
    try:
        costume = parse_costume(text)
        if not costume:
            logger.info("Kanal posti kostum formatiga mos kelmadi, o'tkazib yuborildi.")
            return

        color_code = costume["color_code"]
        normalized = normalize_color_code(color_code)
        if normalized:
            color_code = normalized

        name = costume.get("name", "Noma'lum")
        sizes = costume.get("sizes", "")
        description = costume.get("description", "")
        drop = costume.get("drop", "")

        # Bazada mavjudligini tekshirish
        async with db.db.execute(
            "SELECT id FROM costumes WHERE color_code = ? AND name = ?", 
            (color_code, name)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                costume_id = row[0]
                logger.info(f"[KANAL AUTO-IMPORT] Kostum mavjud: {color_code} | {name}. Rasmlar yangilanmoqda...")
                await db.db.execute(
                    "UPDATE costumes SET mannequin_photos = ? WHERE id = ?",
                    (json.dumps(mannequin_photos), costume_id)
                )
                await db.db.commit()
            else:
                logger.info(f"[KANAL AUTO-IMPORT] Yangi kostum qo'shilmoqda: {color_code} | {name} ({len(mannequin_photos)} ta rasm)")
                await db.add_costume(
                    color_code=color_code,
                    name=name,
                    price="Narx ko'rsatilmagan",
                    sizes=sizes,
                    material="Ko'rsatilmagan",
                    color_description=description,
                    mannequin_photos=mannequin_photos,
                    model_photos=[],
                    extra_note=drop
                )
    except Exception as e:
        logger.error(f"Kanal postini qayta ishlashda xatolik: {e}")


@router.channel_post()
async def handle_channel_post(message: Message, db: Database):
    """Kanaldagi yangi postlarni ushlash."""
    try:
        # Faqat o'zimizning kanaldan kelgan postlarni qabul qilamiz
        if message.chat.id != CHANNEL_ID:
            return

        # Agar xabar media group (album) bo'lsa
        if message.media_group_id:
            mg_id = message.media_group_id
            
            if mg_id not in media_group_cache:
                media_group_cache[mg_id] = {
                    "message_ids": [],
                    "caption": None
                }
                
            media_group_cache[mg_id]["message_ids"].append(message.message_id)
            if message.caption:
                media_group_cache[mg_id]["caption"] = message.caption
                
            # Albomdagi barcha rasmlarni kutib olish uchun 3 soniya kutamiz
            if mg_id not in media_group_locks:
                media_group_locks[mg_id] = True
                await asyncio.sleep(3)
                
                # Cache-dan ma'lumotlarni o'qiymiz va o'chiramiz
                data = media_group_cache.pop(mg_id, None)
                media_group_locks.pop(mg_id, None)
                
                if data and data["caption"]:
                    await process_and_save_costume(data["caption"], sorted(data["message_ids"]), db)
        else:
            # Bitta rasm yoki matnli post bo'lsa
            text = message.caption or message.text
            if text:
                await process_and_save_costume(text, [message.message_id], db)
    except Exception as e:
        logger.error(f"Kanal postini ushlashda xatolik: {e}")
