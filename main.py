"""
KostyumShopBot — Asosiy ishga tushirish fayli.

Telegram bot kostyum do'koni uchun:
- Klientlar color raqam orqali kostum ma'lumotlarini oladi
- Admin bot orqali kostumlarni boshqaradi

Ishga tushirish: python main.py
"""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, DB_PATH
from database import Database
from handlers import get_all_routers
from middlewares.throttling import ThrottlingMiddleware


# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(stream=open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False))]
)
logger = logging.getLogger(__name__)


async def main():
    """Botni ishga tushirish."""

    # Token tekshiruvi
    if not BOT_TOKEN or BOT_TOKEN == "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ":
        logger.error("BOT_TOKEN sozlanmagan! .env faylni tekshiring.")
        sys.exit(1)

    # PythonAnywhere proksi sozlash (bepul rejada kerak)
    session = None
    if "PYTHONANYWHERE_DOMAIN" in os.environ or os.path.exists("/home/ynomanov"):
        proxy_url = "http://proxy.server:3128"
        session = AiohttpSession(proxy=proxy_url)
        logger.info(f"PythonAnywhere aniqlandi, proksi ishlatilmoqda: {proxy_url}")

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Ma'lumotlar bazasini yaratish va ulash
    db = Database(DB_PATH)
    await db.connect()
    logger.info(f"DB ulandi: {DB_PATH}")

    # Middleware qo'shish (flood himoyasi)
    dp.message.middleware(ThrottlingMiddleware())

    # Routerlarni ro'yxatdan o'tkazish
    for router in get_all_routers():
        dp.include_router(router)
    logger.info("Barcha routerlar ro'yxatdan o'tdi")

    # Database ni har bir handlerga uzatish
    dp["db"] = db

    # Botni ishga tushirish
    logger.info("Bot ishga tushmoqda...")
    try:
        # Bot tavsiflari va buyruqlarini o'rnatish
        try:
            from aiogram.types import BotCommand
            await bot.set_my_description(
                "🎩 \"SACO\" premium do'koni mijozlari uchun maxsus raqamli katalog!\n"
                "👔 Kostyum xarid qilishdan oldin uning barcha ko'rinishlari va o'lchamlarini shu yerda ko'ring.\n"
                "🚀 Istalgan color kodini yuboring va mukammal tanlovni amalga oshiring. Boshlash uchun /start bosing!"
            )
            await bot.set_my_short_description(
                "\"SACO\" premium do'koni rasmiy katalogi. Kostyum topish uchun uning color kodini yuboring!"
            )
            await bot.set_my_commands([
                BotCommand(command="start", description="Botni ishga tushirish / boshlash"),
                BotCommand(command="catalog", description="Barcha mavjud kastyumlar"),
                BotCommand(command="favorites", description="Sevimli kastyumlar ro'yxati"),
                BotCommand(command="recent", description="Oxirgi ko'rilganlar"),
                BotCommand(command="help", description="Yordam va qo'llanma"),
            ])
            logger.info("Bot tavsifi va buyruqlari muvaffaqiyatli o'rnatildi")
        except Exception as e:
            logger.warning(f"Bot tavsifini o'rnatishda xatolik: {e}")

        # Webhook o'rniga polling ishlayveradi, lekin Render o'chirib yubormasligi uchun portni ochamiz
        if os.environ.get("RENDER") or os.environ.get("PORT"):
            from aiohttp import web
            async def handle(request):
                return web.Response(text="Bot is running!")
            app = web.Application()
            app.router.add_get('/', handle)
            runner = web.AppRunner(app)
            await runner.setup()
            port = int(os.environ.get("PORT", 8080))
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            logger.info(f"Render dummy web server started on port {port}")

        # Eski update larni o'tkazib yuborish
        await bot.delete_webhook(drop_pending_updates=True)
        # Polling boshlash
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi (Ctrl+C)")
