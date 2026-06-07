"""
Kanaldan kostumlarni import qilish skripti.
Telethon orqali kanaldan postlarni o'qib, bazaga soladi.
Rasmlarni to'g'ridan-to'g'ri kanaldan ko'rsatish uchun ularning message_id'lari saqlanadi.
"""

import asyncio
import re
import sqlite3
import json
from telethon import TelegramClient

# === SOZLAMALAR ===
API_ID = 35764432
API_HASH = "ae2803ec984ed28f4d5bd3befcf0b5c1"
CHANNEL = -1002603849125  # Kanalingiz ID si
DB_PATH = "costume_bot.db"
# ==================

client = TelegramClient("saco_session", API_ID, API_HASH)


def parse_costume(text: str) -> dict | None:
    """Postdan kostum ma'lumotlarini ajratib olish."""
    if not text:
        return None

    data = {}

    # Model nomi
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

    # Tavsif (oxirgi qator)
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if lines:
        data["description"] = lines[-1]

    # Color raqam bo'lmasa skip
    if "color_code" not in data:
        return None

    return data


async def main():
    await client.start()
    print("✅ Telegram ga ulandi!")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Eski ma'lumotlarni o'chirish (tozalash)
    print("🧹 Eski kostyumlar bazadan o'chirilmoqda, kanaldagi yangilari bilan sinxronlash uchun...")
    cursor.execute("DELETE FROM costumes")
    conn.commit()

    imported = 0
    skipped = 0
    errors = 0

    print(f"📥 Kanaldan postlar o'qilmoqda, kuting...")

    # Postlarni guruhlash uchun (media group)
    groups = {}
    standalone = []

    async for message in client.iter_messages(CHANNEL, limit=None):
        if not message.media:
            continue
            
        if message.grouped_id:
            if message.grouped_id not in groups:
                groups[message.grouped_id] = []
            groups[message.grouped_id].append(message)
        else:
            standalone.append([message])

    # Barcha postlarni bitta ro'yxatga jamlaymiz
    all_posts = list(groups.values()) + standalone

    for msgs in all_posts:
        try:
            # Xabarning matnini barcha rasmlardan qidiramiz
            text = ""
            msg_ids = []
            for m in msgs:
                msg_ids.append(m.id)
                if hasattr(m, 'text') and m.text:
                    text += m.text + "\n"

            # Tartiblash (1-xabar eng birinchi bo'lishi uchun)
            msg_ids.sort()

            costume = parse_costume(text)
            if not costume:
                skipped += 1
                continue

            from utils.color_parser import normalize_color_code
            color_code = costume["color_code"]
            normalized = normalize_color_code(color_code)
            if normalized:
                color_code = normalized
            name = costume.get("name", "Noma'lum")
            sizes = costume.get("sizes", "")
            description = costume.get("description", "")
            mannequin_photos = json.dumps(msg_ids) # Rasmlarni json array qilib saqlash

            # Bazada bormi tekshirish (color_code va name bo'yicha)
            cursor.execute("SELECT id FROM costumes WHERE color_code = ? AND name = ?", (color_code, name))
            if cursor.fetchone():
                print(f"⏭ Mavjud: {color_code} — {name} (rasmlari yangilanmoqda...)")
                cursor.execute(
                    "UPDATE costumes SET mannequin_photos = ? WHERE color_code = ? AND name = ?", 
                    (mannequin_photos, color_code, name)
                )
                conn.commit()
                skipped += 1
                continue

            # Bazaga qo'shish
            cursor.execute("""
                INSERT INTO costumes (color_code, name, price, sizes, material, color_description, mannequin_photos, extra_note, is_available)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                color_code,
                name,
                "Narx ko'rsatilmagan",
                sizes,
                "Ko'rsatilmagan",
                description,
                mannequin_photos,
                costume.get("drop", ""),
            ))
            conn.commit()

            imported += 1
            print(f"✅ Qo'shildi: {color_code} — {name} ({len(msg_ids)} ta rasm)")

        except Exception as e:
            errors += 1
            print(f"❌ Xato: {e}")

    conn.close()
    print(f"\n🎉 Tugadi!")
    print(f"✅ Yangi qo'shildi: {imported}")
    print(f"⏭ Mavjudlari yangilandi / o'tkazildi: {skipped}")
    print(f"❌ Xato: {errors}")


if __name__ == "__main__":
    asyncio.run(main())
