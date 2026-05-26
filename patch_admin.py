import re

def patch():
    with open('handlers/admin.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update imports
    if 'get_variants_keyboard' not in content:
        content = content.replace(
            'get_broadcast_confirm_keyboard, get_notify_keyboard',
            'get_broadcast_confirm_keyboard, get_notify_keyboard,\n    get_variants_keyboard'
        )

    # 2. AddCostume process_color_code
    # Warning message if it already exists instead of erroring out
    old_process_color = """@router.message(AddCostume.color_code)
async def process_color_code(message: Message, state: FSMContext, db: Database):
    color = message.text.strip()
    existing = await db.get_costume_any(color)
    if existing:
        await message.answer(f"⚠️ Bu color (<code>{color}</code>) allaqachon mavjud! Boshqasini kiriting:", parse_mode="HTML")
        return
    await state.update_data(color_code=color)
    await state.set_state(AddCostume.name)
    await message.answer("📌 Qadam 2/9\\n👔 Kostum nomini yozing:", parse_mode="HTML")"""

    new_process_color = """@router.message(AddCostume.color_code)
async def process_color_code(message: Message, state: FSMContext, db: Database):
    color = message.text.strip()
    existing = await db.get_costumes_any(color)
    if existing:
        await message.answer(f"⚠️ Bu color (<code>{color}</code>) bilan allaqachon {len(existing)} ta variant bor. Yangi variant qo'shilmoqda.", parse_mode="HTML")
    await state.update_data(color_code=color)
    await state.set_state(AddCostume.name)
    await message.answer("📌 Qadam 2/9\\n👔 Kostum nomini yozing:", parse_mode="HTML")"""
    content = content.replace(old_process_color, new_process_color)

    # 3. _save_costume success message color_code to avoid UNIQUE confusion
    # Actually _save_costume is fine as is.

    # 4. DeleteCostume
    old_delete = """@router.message(DeleteCostume.confirm, F.text, lambda msg: not msg.text.startswith("/"))
async def confirm_delete(message: Message, state: FSMContext, db: Database):
    current = await state.get_state()
    if current != DeleteCostume.confirm:
        return

    color = message.text.strip()
    costume = await db.get_costume_any(color)
    if not costume:
        await message.answer(f"❌ <code>{color}</code> topilmadi!", parse_mode="HTML")
        await state.clear()
        return

    success = await db.delete_costume(color)
    await state.clear()
    if success:
        await message.answer(f"✅ <code>{color}</code> — <b>{costume['name']}</b> o'chirildi!", parse_mode="HTML")
    else:
        await message.answer("❌ Xatolik yuz berdi.")"""

    new_delete = """@router.message(DeleteCostume.confirm, F.text, lambda msg: not msg.text.startswith("/"))
async def confirm_delete(message: Message, state: FSMContext, db: Database):
    current = await state.get_state()
    if current != DeleteCostume.confirm:
        return

    color = message.text.strip()
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
        await message.answer("❌ Xatolik yuz berdi.")"""
    content = content.replace(old_delete, new_delete)

    # 5. EditCostume
    old_edit_select = """@router.message(EditCostume.select_color)
async def edit_select_color(message: Message, state: FSMContext, db: Database):
    color = message.text.strip()
    costume = await db.get_costume_any(color)
    if not costume:
        await message.answer(f"❌ <code>{color}</code> topilmadi!", parse_mode="HTML")
        await state.clear()
        return

    await state.update_data(edit_color=color)
    await state.set_state(EditCostume.select_field)
    await message.answer(
        f"✏️ <b>{costume['name']}</b> (<code>{color}</code>)\\n\\nQaysi maydonni tahrirlaysiz?",
        parse_mode="HTML", reply_markup=get_edit_fields_keyboard(color)
    )"""

    new_edit_select = """@router.message(EditCostume.select_color)
async def edit_select_color(message: Message, state: FSMContext, db: Database):
    color = message.text.strip()
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
        f"✏️ <b>{costume['name']}</b> (<code>{costume['color_code']}</code>)\\n\\nQaysi maydonni tahrirlaysiz?",
        parse_mode="HTML", reply_markup=get_edit_fields_keyboard(costume["id"])
    )"""
    content = content.replace(old_edit_select, new_edit_select)

    old_edit_field_1 = """@router.callback_query(F.data.startswith("edit_field:"))
async def edit_select_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    field = parts[1]
    color = parts[2] if len(parts) > 2 else ""

    await state.update_data(edit_field=field, edit_color=color)"""
    new_edit_field_1 = """@router.callback_query(F.data.startswith("edit_field:"))
async def edit_select_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    field = parts[1]
    # We already have edit_costume_id in state, but it is passed just in case
    
    await state.update_data(edit_field=field)"""
    content = content.replace(old_edit_field_1, new_edit_field_1)

    old_edit_val = """@router.message(EditCostume.new_value)
async def edit_new_value(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    field = data.get("edit_field")
    color = data.get("edit_color")

    success = await db.update_costume(color, **{field: message.text.strip()})
    await state.clear()

    if success:
        await message.answer(f"✅ <code>{color}</code> muvaffaqiyatli yangilandi!", parse_mode="HTML")
    else:
        await message.answer("❌ Xatolik yuz berdi.")"""
    new_edit_val = """@router.message(EditCostume.new_value)
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
        await message.answer("❌ Xatolik yuz berdi.")"""
    content = content.replace(old_edit_val, new_edit_val)

    old_edit_photo = """@router.message(EditCostume.new_photos, Command("done"))
async def edit_photos_done(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    photos = data.get("new_photos", [])
    if not photos:
        await message.answer("⚠️ Kamida 1 ta rasm yuboring!")
        return
    field = data.get("edit_field")
    color = data.get("edit_color")
    success = await db.update_costume(color, **{field: photos})
    await state.clear()
    if success:
        await message.answer(f"✅ Rasmlar yangilandi! (<code>{color}</code>)", parse_mode="HTML")
    else:
        await message.answer("❌ Xatolik yuz berdi.")"""
    new_edit_photo = """@router.message(EditCostume.new_photos, Command("done"))
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
        await message.answer("❌ Xatolik yuz berdi.")"""
    content = content.replace(old_edit_photo, new_edit_photo)


    # 6. Toggle Costume
    old_toggle = """@router.message(Command("toggle_costume"))
@router.callback_query(F.data == "admin:toggle")
async def start_toggle(event: Union[Message, CallbackQuery], state: FSMContext):
    if not is_admin(event.from_user.id):
        return
    text = "🔄 Aktiv/nofaol qilish uchun color raqamini yuboring:"
    await state.set_data({"action": "toggle"})
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=get_cancel_keyboard())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_cancel_keyboard())"""
    new_toggle = """class ToggleCostume(StatesGroup):
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
        await message.answer("❌ Xatolik yuz berdi.")"""
    
    if "class ToggleCostume" not in content:
        content = content.replace(old_toggle, new_toggle)
        # Import StatesGroup and State if not present
        if "from aiogram.fsm.state import StatesGroup, State" not in content:
            content = content.replace("from aiogram.fsm.context import FSMContext", "from aiogram.fsm.context import FSMContext\nfrom aiogram.fsm.state import StatesGroup, State")

    with open('handlers/admin.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("handlers/admin.py patched successfully!")

if __name__ == "__main__":
    patch()
