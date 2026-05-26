"""
Konfiguratsiya moduli.
.env fayldan muhit o'zgaruvchilarini o'qiydi va
bot sozlamalarini saqlaydi.
"""

import os
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()
_channel_id_str = os.getenv('CHANNEL_ID', '')
CHANNEL_ID = int(_channel_id_str) if _channel_id_str.lstrip('-').isdigit() else _channel_id_str


# ═══════════════════════════════════════════════
# Bot sozlamalari
# ═══════════════════════════════════════════════

# Telegram Bot Token
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Admin Telegram ID lari (list[int])
ADMIN_IDS: list[int] = [
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip().isdigit()
]

# Ma'lumotlar bazasi fayl yo'li
DB_PATH: str = os.getenv("DB_PATH", "costume_bot.db")

# Admin kontakt (klient uchun ko'rsatiladi)
ADMIN_CONTACT: str = os.getenv("ADMIN_CONTACT", "@admin")


# ═══════════════════════════════════════════════
# Cheklovlar
# ═══════════════════════════════════════════════

# Flood himoyasi: 1 daqiqada maksimal so'rov soni
RATE_LIMIT: int = 10
RATE_LIMIT_PERIOD: int = 60  # soniya

# Har bir turdagi maksimal rasm soni
MAX_PHOTOS_PER_TYPE: int = 5

# Oxirgi ko'rilganlar soni
RECENT_LIMIT: int = 5


# ═══════════════════════════════════════════════
# Xabar shablonlari
# ═══════════════════════════════════════════════

START_MESSAGE = """
💼 <b>"SACO" premium erkaklar do'koniga xush kelibsiz!</b>

👔 Bizda eng so'nggi urfdagi dvoyka va troyka kostyum-shimlar kolleksiyasi mavjud.
🔍 Kostyum rasmlarini ko'rish uchun uning <b>color kodini</b> (masalan, <code>23/33</code>) yuboring!

📋 <b>Barcha mahsulotlar katalogi:</b> /catalog
"""

HELP_MESSAGE = """
❓ <b>Qo'llab-quvvatlash va Qo'llanma</b>

📌 <b>Kostyumni tezkor qidirish:</b>
Menga shunchaki color kodini yuboring. Quyidagi qulay formatlarda yuborishingiz mumkin:
• <code>23/33</code> — standart ko'rinish
• <code>23 33</code> — bo'sh joy bilan
• <code>2333</code> — slashsiz yaxlit ko'rinish
• <code>#23/33</code> — hashtag bilan
• <code>color 23/33</code> — har qanday matn ichida

📋 <b>Bot buyruqlari:</b>
/start — Botni boshlash / Bosh sahifa
/help — Yordam va ma'lumotlar
/catalog — Barcha mavjud modellar katalogi
/favorites — Sizga yoqqan modellar ro'yxati
/recent — Oxirgi ko'rgan mahsulotlaringiz

⚡ <b>Sizning shaxsiy stilistingiz:</b> {contact}
<i>Kattalikni aniqlash, buyurtma berish va yetkazib berish bo'yicha savollaringizga mamnuniyat bilan javob beramiz!</i>
"""

NOT_FOUND_MESSAGE = """
🔍 <b>Kechirasiz, ushbu color kodli kostyum hozirda omborimizda tugagan bo'lishi mumkin.</b>

Xavotir olmang! Biz siz uchun eng mos va chiroyli modellarni tanlashga yordam beramiz.
📋 Hozirda sotuvda mavjud barcha to'plamlarni ko'rish: /catalog
📞 Yoki mutaxassisimiz bilan bog'lanib, shaxsiy buyurtma bering: {contact}
"""

COSTUME_INFO_TEMPLATE = """
🎩 <b>SACO</b>
──────────────────────────
🎨 <b>Color:</b> <code>{color_code}</code>
✨ <b>Model:</b> <b>{name}</b>
💧 <b>Drop:</b> <code>{drop}</code>
📏 <b>Razmer:</b> <code>{sizes}</code>
👔 <b>Turi:</b> <b>{suit_type}</b>
📦 <b>Soni:</b> <code>{stock_qty}</code>
📍 <b>Qator:</b> <code>{warehouse_location}</code>
──────────────────────────
"""
