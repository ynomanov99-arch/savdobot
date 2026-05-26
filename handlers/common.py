"""
Umumiy handlerlar moduli.
Noma'lum xabarlar va umumiy callback querylar uchun handlerlar.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

router = Router(name="common")


@router.callback_query(F.data == "start")
async def callback_start(callback: CallbackQuery, state: FSMContext):
    """Bosh sahifa tugmasi bosilganda — /start ga o'xshash javob."""
    await state.clear()

    from config import START_MESSAGE
    from keyboards.reply import get_main_menu

    await callback.message.answer(
        START_MESSAGE,
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Bekor qilish tugmasi — FSM holatini tozalash."""
    await state.clear()
    await callback.message.answer(
        "❌ Amal bekor qilindi.",
        parse_mode="HTML"
    )
    await callback.answer()
