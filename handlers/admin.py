"""
Admin handlerlari moduli.
Kostum qo'shish, tahrirlash, o'chirish, statistika, broadcast, excel eksport.
"""
import io
import logging
import os
from datetime import datetime
from typing import Union

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import ADMIN_IDS, ADMIN_CONTACT, MAX_PHOTOS_PER_TYPE
from database import Database
from states.admin_states import AddCostume, EditCostume, BroadcastState, DeleteCostume
from keyboards.inline import (
    get_admin_menu, get_edit_fields_keyboard,
    get_confirm_keyboard, get_cancel_keyboard,
    get_broadcast_confirm_keyboard, get_notify_keyboard,
    get_variants_keyboard
)

logger = logging.getLogger(__name__)
router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ═══════════════════════════════════════════════
# Admin tekshiruvi filtri
# ═══════════════════════════════════════════════

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Bu buyruq faqat adminlar uchun.")
        return
    await message.answer(
        "🔧 <b>Admin Panel</b>\n\nQuyidagi amallardan birini tanlang:",
        parse_mode="HTML", reply_markup=get_admin_menu()
    )


# ═══════════════════════════════════════════════
# Kostum qo'shish (Step-by-step FSM)
# ═══════════════════════════════════════════════

@router.message(Command("add_costume"))
@router.callback_query(F.data == "admin:add")
async def start_add_costume(event: Union[Message, CallbackQuery], state: FSMContext):
    user_id = event.from_user.id
    if not is_admin(user_id):
        if isinstance(event, CallbackQuery):
            await event.answer("⛔ Faqat admin!", show_alert=True)
        return

    await state.set_state(AddCostume.color_code)
    await state.update_data(mannequin_photos=[], model_photos=[])

    text = "➕ <b>Yangi kostum qo'shish</b>\n\n📌 Qadam 1/9\nColor raqamini yuboring (masalan: <code>23/33</code>):"
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())


@router.message(AddCostume.color_code)
async def process_color_code(message: Message, state: FSMContext, db: Database):
    color = message.text.strip()
    from utils.color_parser import normalize_color_code
    normalized = normalize_color_code(color)
    if normalized:
        color = normalized
    existing = await db.get_costumes_any(color)
    if existing:
        await message.answer(f"⚠️ Bu color (<code>{color}</code>) bilan allaqachon {len(existing)} ta variant bor. Yangi variant qo'shilmoqda.", parse_mode="HTML")
    await state.update_data(color_code=color)
    await state.set_state(AddCostume.name)
    await message.answer("📌 Qadam 2/9\n👔 Kostum nomini yozing:", parse_mode="HTML")


@router.message(AddCostume.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddCostume.price)
    await message.answer("📌 Qadam 3/9\n💰 Narxini yozing (masalan: <code>850,000 so'm</code>):", parse_mode="HTML")


@router.message(AddCostume.price)
async def process_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text.strip())
    await state.set_state(AddCostume.sizes)
    await message.answer("📌 Qadam 4/9\n📏 Mavjud o'lchamlarni yozing (vergul bilan, masalan: <code>46, 48, 50, 52</code>):", parse_mode="HTML")


@router.message(AddCostume.sizes)
async def process_sizes(message: Message, state: FSMContext):
    await state.update_data(sizes=message.text.strip())
    await state.set_state(AddCostume.material)
    await message.answer("📌 Qadam 5/9\n🧵 Material tarkibini yozing (masalan: <code>80% jun, 20% poliyester</code>):", parse_mode="HTML")


@router.message(AddCostume.material)
async def process_material(message: Message, state: FSMContext):
    await state.update_data(material=message.text.strip())
    await state.set_state(AddCostume.color_description)
    await message.answer("📌 Qadam 6/9\n🎨 Rang va uslub tavsifini yozing:", parse_mode="HTML")


@router.message(AddCostume.color_description)
async def process_color_desc(message: Message, state: FSMContext):
    await state.update_data(color_description=message.text.strip())
    await state.set_state(AddCostume.mannequin_photos)
    await message.answer(
        "📌 Qadam 7/9\n📸 Maneken/shim rasmlarini yuboring (birma-bir, 1-5 ta).\n"
        "Tugagach <code>/done</code> yozing:",
        parse_mode="HTML"
    )


@router.message(AddCostume.mannequin_photos, F.photo)
async def process_mannequin_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("mannequin_photos", [])
    if len(photos) >= MAX_PHOTOS_PER_TYPE:
        await message.answer(f"⚠️ Maksimal {MAX_PHOTOS_PER_TYPE} ta rasm!")
        return
    photo_id = message.photo[-1].file_id
    photos.append(photo_id)
    await state.update_data(mannequin_photos=photos)
    await message.answer(f"✅ Rasm qabul qilindi ({len(photos)}/{MAX_PHOTOS_PER_TYPE}). Yana yuboring yoki /done bosing.")


@router.message(AddCostume.mannequin_photos, Command("done"))
async def mannequin_done(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("mannequin_photos"):
        await message.answer("⚠️ Kamida 1 ta rasm yuboring!")
        return
    await state.set_state(AddCostume.model_photos)
    await message.answer(
        "📌 Qadam 8/9\n🧍 Erkak model rasmlarini yuboring (birma-bir, 1-5 ta).\n"
        "Tugagach <code>/done</code> yozing:",
        parse_mode="HTML"
    )


@router.message(AddCostume.model_photos, F.photo)
async def process_model_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("model_photos", [])
    if len(photos) >= MAX_PHOTOS_PER_TYPE:
        await message.answer(f"⚠️ Maksimal {MAX_PHOTOS_PER_TYPE} ta rasm!")
        return
    photo_id = message.photo[-1].file_id
    photos.append(photo_id)
    await state.update_data(model_photos=photos)
    await message.answer(f"✅ Rasm qabul qilindi ({len(photos)}/{MAX_PHOTOS_PER_TYPE}). Yana yuboring yoki /done bosing.")


@router.message(AddCostume.model_photos, Command("done"))
async def model_done(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("model_photos"):
        await message.answer("⚠️ Kamida 1 ta rasm yuboring!")
        return
    await state.set_state(AddCostume.extra_note)
    await message.answer("📌 Qadam 9/9\n📝 Qo'shimcha izoh bormi? (bo'lmasa /skip yozing):", parse_mode="HTML")


@router.message(AddCostume.extra_note, Command("skip"))
async def skip_extra_note(message: Message, state: FSMContext, db: Database, bot: Bot):
    await state.update_data(extra_note="")
    await _save_costume(message, state, db, bot)


@router.message(AddCostume.extra_note)
async def process_extra_note(message: Message, state: FSMContext, db: Database, bot: Bot):
    if message.text and message.text.startswith('/'):
        return
    await state.update_data(extra_note=message.text.strip())
    await _save_costume(message, state, db, bot)


async def _save_costume(message: Message, state: FSMContext, db: Database, bot: Bot):
    data = await state.get_data()
    success = await db.add_costume(
        color_code=data["color_code"], name=data["name"],
        price=data["price"], sizes=data["sizes"],
        material=data["material"], color_description=data["color_description"],
        mannequin_photos=data["mannequin_photos"],
        model_photos=data["model_photos"],
        extra_note=data.get("extra_note", "")
    )
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>Kostum muvaffaqiyatli qo'shildi!</b>\n\n"
            f"🎨 Color: <code>{data['color_code']}</code>\n"
            f"👔 Nomi: {data['name']}",
            parse_mode="HTML", reply_markup=get_notify_keyboard()
        )
        await state.update_data(last_added_color=data["color_code"])
    else:
        await message.answer("❌ Xatolik! Bu color raqam allaqachon mavjud.", parse_mode="HTML")


@router.callback_query(F.data == "notify:yes")
async def notify_users(callback: CallbackQuery, db: Database, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    user_ids = await db.get_all_user_ids()
    sent = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid,
                "🆕 <b>Yangi kostum qo'shildi!</b>\nBatafsil ma'lumot uchun /catalog bosing.",
                parse_mode="HTML")
            sent += 1
        except Exception:
            pass
    await callback.message.answer(f"📢 {sent}/{len(user_ids)} foydalanuvchiga xabar yuborildi.")
    await callback.answer()


@router.callback_query(F.data == "notify:no")
async def skip_notify(callback: CallbackQuery):
    await callback.answer("OK, xabar yuborilmadi.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


# ═══════════════════════════════════════════════
# Kostumlar ro'yxati
# ═══════════════════════════════════════════════

@router.message(Command("list_costumes"))
@router.callback_query(F.data == "admin:list")
async def list_costumes(event: Union[Message, CallbackQuery], db: Database):
    if not is_admin(event.from_user.id):
        return
    costumes = await db.list_costumes()
    if not costumes:
        text = "📋 Hozircha hech qanday kostum yo'q."
    else:
        text = "📋 <b>Barcha kostumlar:</b>\n\n"
        for c in costumes:
            status = "✅" if c["is_available"] else "❌"
            text += f"{status} <code>{c['color_code']}</code> — {c['name']} | {c['price']}\n"
        text += f"\n📊 Jami: {len(costumes)} ta"

    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML")


# ═══════════════════════════════════════════════
# Kostumni o'chirish
# ═══════════════════════════════════════════════

@router.message(Command("delete_costume"))
@router.callback_query(F.data == "admin:delete")
async def start_delete(event: Union[Message, CallbackQuery], state: FSMContext):
    if not is_admin(event.from_user.id):
        return
    from states.admin_states import DeleteCostume
    await state.set_state(DeleteCostume.confirm)
    text = "🗑 O'chirish uchun color raqamini yuboring:"
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=get_cancel_keyboard())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_cancel_keyboard())


@router.message(DeleteCostume.confirm, F.text, lambda msg: not msg.text.startswith("/"))
async def confirm_delete(message: Message, state: FSMContext, db: Database):
    current = await state.get_state()
    if current != DeleteCostume.confirm:
        return

    color = message.text.strip()
    from utils.color_parser import normalize_color_code
    normalized = normalize_color_code(color)
    if normalized:
        color = normalized
    costumes = await db.get_costumes_any(color)
    if not costumes:
        await message.answer(f"❌ <code>{color}</code> topilmadi!", parse_mode="HTML")
        await state.clear()
        return

    if len(costumes) == 1:
        await process_delete_costume(message, costumes[0], db)
    else:
        await message.answer("Bir nechta variant topildi. Qaysi birini o'chirasiz?", reply_markup=get_variants_keyboard(costumes, prefix="admin_del_var"))
    await state.clear()

@router.callback_query(F.data.startswith("admin_del_var:"))
async def admin_del_var_callback(callback: CallbackQuery, db: Database):
    costume_id = int(callback.data.split(":")[1])
    costume = await db.get_costume_by_id(costume_id)
    if costume:
        await process_delete_costume(callback.message, costume, db)
    await callback.answer()

async def process_delete_costume(message: Message, costume: dict, db: Database):
    success = await db.delete_costume(costume["id"])
    if success:
        await message.answer(f"✅ <code>{costume['color_code']}</code> — <b>{costume['name']}</b> o'chirildi!", parse_mode="HTML")
    else:
        await message.answer("❌ Xatolik yuz berdi.")


# ═══════════════════════════════════════════════
# Kostumni tahrirlash
# ═══════════════════════════════════════════════

@router.message(Command("edit_costume"))
@router.callback_query(F.data == "admin:edit")
async def start_edit(event: Union[Message, CallbackQuery], state: FSMContext):
    if not is_admin(event.from_user.id):
        return
    await state.set_state(EditCostume.select_color)
    text = "✏️ Tahrirlash uchun color raqamini yuboring:"
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=get_cancel_keyboard())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_cancel_keyboard())


@router.message(EditCostume.select_color)
async def edit_select_color(message: Message, state: FSMContext, db: Database):
    color = message.text.strip()
    from utils.color_parser import normalize_color_code
    normalized = normalize_color_code(color)
    if normalized:
        color = normalized
    costumes = await db.get_costumes_any(color)
    if not costumes:
        await message.answer(f"❌ <code>{color}</code> topilmadi!", parse_mode="HTML")
        await state.clear()
        return

    if len(costumes) == 1:
        await _prompt_edit_fields(message, state, costumes[0])
    else:
        await message.answer("Bir nechta variant topildi. Qaysi birini tahrirlaysiz?", reply_markup=get_variants_keyboard(costumes, prefix="admin_edit_var"))

@router.callback_query(F.data.startswith("admin_edit_var:"))
async def admin_edit_var_callback(callback: CallbackQuery, state: FSMContext, db: Database):
    costume_id = int(callback.data.split(":")[1])
    costume = await db.get_costume_by_id(costume_id)
    if not costume:
        await callback.answer("Topilmadi", show_alert=True)
        return
    await _prompt_edit_fields(callback.message, state, costume)
    await callback.answer()

async def _prompt_edit_fields(message: Message, state: FSMContext, costume: dict):
    await state.update_data(edit_costume_id=costume["id"], edit_color=costume["color_code"])
    await state.set_state(EditCostume.select_field)
    await message.answer(
        f"✏️ <b>{costume['name']}</b> (<code>{costume['color_code']}</code>)\n\nQaysi maydonni tahrirlaysiz?",
        parse_mode="HTML", reply_markup=get_edit_fields_keyboard(costume["id"])
    )


@router.callback_query(F.data.startswith("edit_field:"))
async def edit_select_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    field = parts[1]
    # We already have edit_costume_id in state, but it is passed just in case
    
    await state.update_data(edit_field=field)

    if field in ("mannequin_photos", "model_photos"):
        await state.set_state(EditCostume.new_photos)
        await state.update_data(new_photos=[])
        await callback.message.answer(
            f"📸 Yangi rasmlarni yuboring (eski rasmlar almashtiriladi).\nTugagach /done bosing:",
            reply_markup=get_cancel_keyboard()
        )
    else:
        await state.set_state(EditCostume.new_value)
        field_names = {
            "name": "👔 Nomi", "price": "💰 Narxi", "sizes": "📏 O'lchamlar",
            "material": "🧵 Material", "color_description": "🎨 Rang tavsifi",
            "extra_note": "📝 Qo'shimcha izoh"
        }
        await callback.message.answer(
            f"✏️ {field_names.get(field, field)} uchun yangi qiymatni yozing:",
            reply_markup=get_cancel_keyboard()
        )
    await callback.answer()


@router.message(EditCostume.new_value)
async def edit_new_value(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    field = data.get("edit_field")
    costume_id = data.get("edit_costume_id")
    color = data.get("edit_color")

    success = await db.update_costume(costume_id, **{field: message.text.strip()})
    await state.clear()

    if success:
        await message.answer(f"✅ <code>{color}</code> muvaffaqiyatli yangilandi!", parse_mode="HTML")
    else:
        await message.answer("❌ Xatolik yuz berdi.")


@router.message(EditCostume.new_photos, F.photo)
async def edit_new_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("new_photos", [])
    if len(photos) >= MAX_PHOTOS_PER_TYPE:
        await message.answer(f"⚠️ Maksimal {MAX_PHOTOS_PER_TYPE} ta!")
        return
    photos.append(message.photo[-1].file_id)
    await state.update_data(new_photos=photos)
    await message.answer(f"✅ Rasm qabul qilindi ({len(photos)}/{MAX_PHOTOS_PER_TYPE}). /done")


@router.message(EditCostume.new_photos, Command("done"))
async def edit_photos_done(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    photos = data.get("new_photos", [])
    if not photos:
        await message.answer("⚠️ Kamida 1 ta rasm yuboring!")
        return
    field = data.get("edit_field")
    costume_id = data.get("edit_costume_id")
    color = data.get("edit_color")
    success = await db.update_costume(costume_id, **{field: photos})
    await state.clear()
    if success:
        await message.answer(f"✅ Rasmlar yangilandi! (<code>{color}</code>)", parse_mode="HTML")
    else:
        await message.answer("❌ Xatolik yuz berdi.")


# ═══════════════════════════════════════════════
# Toggle (aktiv/nofaol)
# ═══════════════════════════════════════════════

class ToggleCostume(StatesGroup):
    color = State()

@router.message(Command("toggle_costume"))
@router.callback_query(F.data == "admin:toggle")
async def start_toggle(event: Union[Message, CallbackQuery], state: FSMContext):
    if not is_admin(event.from_user.id):
        return
    text = "🔄 Aktiv/nofaol qilish uchun color raqamini yuboring:"
    await state.set_state(ToggleCostume.color)
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=get_cancel_keyboard())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_cancel_keyboard())

@router.message(ToggleCostume.color, F.text, lambda msg: not msg.text.startswith("/"))
async def process_toggle(message: Message, state: FSMContext, db: Database):
    color = message.text.strip()
    from utils.color_parser import normalize_color_code
    normalized = normalize_color_code(color)
    if normalized:
        color = normalized
    costumes = await db.get_costumes_any(color)
    if not costumes:
        await message.answer(f"❌ <code>{color}</code> topilmadi!", parse_mode="HTML")
        await state.clear()
        return

    if len(costumes) == 1:
        await _process_toggle_costume(message, costumes[0], db)
    else:
        await message.answer("Bir nechta variant topildi. Qaysi birini o'zgartirasiz?", reply_markup=get_variants_keyboard(costumes, prefix="admin_toggle_var"))
    await state.clear()

@router.callback_query(F.data.startswith("admin_toggle_var:"))
async def admin_toggle_var_callback(callback: CallbackQuery, db: Database):
    costume_id = int(callback.data.split(":")[1])
    costume = await db.get_costume_by_id(costume_id)
    if costume:
        await _process_toggle_costume(callback.message, costume, db)
    await callback.answer()

async def _process_toggle_costume(message: Message, costume: dict, db: Database):
    new_status = await db.toggle_costume(costume["id"])
    if new_status is not None:
        status_text = "✅ Aktivlashtirildi" if new_status else "❌ Nofaol qilindi"
        await message.answer(f"<code>{costume['color_code']}</code> — {status_text}!", parse_mode="HTML")
    else:
        await message.answer("❌ Xatolik yuz berdi.")


# ═══════════════════════════════════════════════
# Statistika
# ═══════════════════════════════════════════════

@router.message(Command("stats"))
@router.callback_query(F.data == "admin:stats")
async def show_stats(event: Union[Message, CallbackQuery], db: Database):
    if not is_admin(event.from_user.id):
        return

    stats = await db.get_stats()
    text = (
        "📊 <b>Bot Statistikasi</b>\n"
        "─────────────────────\n"
        f"👥 Foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"👔 Jami kostumlar: <b>{stats['total_costumes']}</b>\n"
        f"✅ Mavjud kostumlar: <b>{stats['available_costumes']}</b>\n"
        f"🔍 Jami qidiruvlar: <b>{stats['total_searches']}</b>\n"
        f"✅ Muvaffaqiyatli: <b>{stats['successful_searches']}</b>\n"
        f"📅 Bugungi: <b>{stats['today_searches']}</b>\n"
    )

    if stats.get("top_searched"):
        text += "\n🏆 <b>Eng ko'p qidirilgan:</b>\n"
        for code, cnt in stats["top_searched"]:
            text += f"  • <code>{code}</code> — {cnt} marta\n"

    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML")


# ═══════════════════════════════════════════════
# Broadcast
# ═══════════════════════════════════════════════

@router.message(Command("broadcast"))
@router.callback_query(F.data == "admin:broadcast")
async def start_broadcast(event: Union[Message, CallbackQuery], state: FSMContext):
    if not is_admin(event.from_user.id):
        return
    await state.set_state(BroadcastState.message)
    text = "📢 <b>Broadcast</b>\n\nBarcha foydalanuvchilarga yuboriladigan xabarni yozing:"
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())


@router.message(BroadcastState.message)
async def broadcast_message(message: Message, state: FSMContext):
    await state.update_data(broadcast_text=message.text)
    await state.set_state(BroadcastState.confirm)
    await message.answer(
        f"📢 Quyidagi xabar barchaga yuboriladi:\n\n{message.text}\n\nTasdiqlaysizmi?",
        reply_markup=get_broadcast_confirm_keyboard()
    )


@router.callback_query(F.data == "broadcast:confirm")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()

    if not text:
        await callback.answer("Xabar bo'sh!", show_alert=True)
        return

    user_ids = await db.get_all_user_ids()
    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1

    await callback.message.answer(
        f"📢 <b>Broadcast tugadi!</b>\n✅ Yuborildi: {sent}\n❌ Xatolik: {failed}",
        parse_mode="HTML"
    )
    await callback.answer()


# ═══════════════════════════════════════════════
# Excel eksport
# ═══════════════════════════════════════════════

@router.message(Command("export_excel"))
@router.callback_query(F.data == "admin:export")
async def export_excel(event: Union[Message, CallbackQuery], db: Database):
    if not is_admin(event.from_user.id):
        return

    try:
        from openpyxl import Workbook

        costumes = await db.get_all_costumes_for_export()
        wb = Workbook()
        ws = wb.active
        ws.title = "Kostumlar"

        headers = ["Color", "Nomi", "Narxi", "O'lchamlar", "Material",
                    "Rang tavsifi", "Izoh", "Maneken rasmlari", "Model rasmlari", "Mavjud", "Yaratilgan"]
        ws.append(headers)

        for c in costumes:
            ws.append([
                c["color_code"], c["name"], c["price"], c["sizes"],
                c["material"], c["color_description"], c.get("extra_note", ""),
                c["mannequin_photos_count"], c["model_photos_count"],
                "Ha" if c["is_available"] else "Yo'q", str(c.get("created_at", ""))
            ])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        file = BufferedInputFile(buffer.read(), filename=f"kostumlar_{datetime.now().strftime('%Y%m%d')}.xlsx")

        msg = event.message if isinstance(event, CallbackQuery) else event
        await msg.answer_document(file, caption="📥 Kostumlar ro'yxati (Excel)")

        if isinstance(event, CallbackQuery):
            await event.answer()
    except ImportError:
        msg = event.message if isinstance(event, CallbackQuery) else event
        await msg.answer("❌ openpyxl kutubxonasi o'rnatilmagan!\n<code>pip install openpyxl</code>", parse_mode="HTML")
