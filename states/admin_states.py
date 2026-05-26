"""
Admin FSM holatlari (Finite State Machine).
Kostum qo'shish va tahrirlash uchun step-by-step jarayon holatlari.
"""

from aiogram.fsm.state import State, StatesGroup


class AddCostume(StatesGroup):
    """Yangi kostum qo'shish holatlari (9 qadam)."""

    # Qadam 1: Color raqamini yuboring
    color_code = State()

    # Qadam 2: Kostum nomini yozing
    name = State()

    # Qadam 3: Narxini yozing
    price = State()

    # Qadam 4: O'lchamlarni yozing
    sizes = State()

    # Qadam 5: Material tarkibini yozing
    material = State()

    # Qadam 6: Rang va uslub tavsifini yozing
    color_description = State()

    # Qadam 7: Maneken rasmlarini yuboring (/done tugagach)
    mannequin_photos = State()

    # Qadam 8: Model rasmlarini yuboring (/done tugagach)
    model_photos = State()

    # Qadam 9: Qo'shimcha izoh (/skip yoki matn)
    extra_note = State()


class EditCostume(StatesGroup):
    """Kostumni tahrirlash holatlari."""

    # Tahrirlash uchun color raqamni tanlash
    select_color = State()

    # Qaysi maydonni tahrirlash kerak
    select_field = State()

    # Yangi qiymatni kiritish
    new_value = State()

    # Yangi rasmlarni kiritish (agar rasm maydoni tanlansa)
    new_photos = State()


class DeleteCostume(StatesGroup):
    """Kostumni o'chirish holatlari."""

    # Tasdiqlash
    confirm = State()


class BroadcastState(StatesGroup):
    """Broadcast xabar yuborish holatlari."""

    # Xabar matnini kiritish
    message = State()

    # Tasdiqlash
    confirm = State()
