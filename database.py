"""
Ma'lumotlar bazasi moduli.
SQLite bilan asinxron ishlash uchun barcha CRUD operatsiyalari.
"""

import json
import aiosqlite
from datetime import datetime
from typing import Optional


class Database:
    """Asinxron SQLite ma'lumotlar bazasi bilan ishlash klassi."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Ma'lumotlar bazasiga ulanish."""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.db.execute("PRAGMA foreign_keys=ON")
        await self.init_db()

    async def close(self):
        """Ma'lumotlar bazasini yopish."""
        if self.db:
            await self.db.close()

    async def init_db(self):
        """Jadvallarni yaratish (agar mavjud bo'lmasa)."""
        await self.db.executescript("""
            CREATE TABLE IF NOT EXISTS costumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                color_code TEXT NOT NULL,
                name TEXT NOT NULL,
                price TEXT NOT NULL,
                sizes TEXT NOT NULL,
                material TEXT NOT NULL,
                color_description TEXT NOT NULL,
                mannequin_photos TEXT DEFAULT '[]',
                model_photos TEXT DEFAULT '[]',
                extra_note TEXT DEFAULT '',
                is_available BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT DEFAULT '',
                full_name TEXT DEFAULT '',
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT NOT NULL,
                color_code TEXT DEFAULT '',
                found BOOLEAN DEFAULT 0,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                costume_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (costume_id) REFERENCES costumes(id) ON DELETE CASCADE,
                UNIQUE(user_id, costume_id)
            );

            CREATE INDEX IF NOT EXISTS idx_costumes_color ON costumes(color_code);
            CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id);
            CREATE INDEX IF NOT EXISTS idx_search_logs_user ON search_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
        """)
        await self.db.commit()

    # ═══════════════════════════════════════════════
    # Foydalanuvchilar bilan ishlash
    # ═══════════════════════════════════════════════

    async def register_user(self, telegram_id: int, username: str = "", full_name: str = "") -> int:
        """
        Foydalanuvchini ro'yxatdan o'tkazish yoki mavjudini yangilash.
        Foydalanuvchi ID sini qaytaradi.
        """
        cursor = await self.db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()

        if row:
            await self.db.execute(
                "UPDATE users SET username = ?, full_name = ? WHERE telegram_id = ?",
                (username, full_name, telegram_id)
            )
            await self.db.commit()
            return row["id"]
        else:
            cursor = await self.db.execute(
                "INSERT INTO users (telegram_id, username, full_name) VALUES (?, ?, ?)",
                (telegram_id, username, full_name)
            )
            await self.db.commit()
            return cursor.lastrowid

    async def get_all_user_ids(self) -> list[int]:
        """Barcha foydalanuvchilarning Telegram ID larini qaytaradi (broadcast uchun)."""
        cursor = await self.db.execute("SELECT telegram_id FROM users")
        rows = await cursor.fetchall()
        return [row["telegram_id"] for row in rows]

    async def get_user_count(self) -> int:
        """Jami foydalanuvchilar sonini qaytaradi."""
        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM users")
        row = await cursor.fetchone()
        return row["cnt"]

    # ═══════════════════════════════════════════════
    # Kostumlar bilan ishlash (CRUD)
    # ═══════════════════════════════════════════════

    async def add_costume(
        self,
        color_code: str,
        name: str,
        price: str,
        sizes: str,
        material: str,
        color_description: str,
        mannequin_photos: list[str],
        model_photos: list[str],
        extra_note: str = ""
    ) -> bool:
        """
        Yangi kostum qo'shish.
        Muvaffaqiyatli bo'lsa True, color_code takroriy bo'lsa False qaytaradi.
        """
        try:
            await self.db.execute(
                """INSERT INTO costumes 
                (color_code, name, price, sizes, material, color_description,
                 mannequin_photos, model_photos, extra_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    color_code, name, price, sizes, material, color_description,
                    json.dumps(mannequin_photos),
                    json.dumps(model_photos),
                    extra_note
                )
            )
            await self.db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def get_costumes(self, color_code: str) -> list[dict]:
        """
        Color code bo'yicha barcha mavjud kostumlarni topish.
        """
        cursor = await self.db.execute(
            "SELECT * FROM costumes WHERE color_code = ? AND is_available = 1",
            (color_code,)
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            costume = dict(row)
            costume["mannequin_photos"] = json.loads(costume["mannequin_photos"])
            costume["model_photos"] = json.loads(costume["model_photos"])
            result.append(costume)
        return result

    async def get_costume_by_id(self, costume_id: int) -> Optional[dict]:
        """ID bo'yicha kostumni topish."""
        cursor = await self.db.execute(
            "SELECT * FROM costumes WHERE id = ?",
            (costume_id,)
        )
        row = await cursor.fetchone()
        if row:
            costume = dict(row)
            costume["mannequin_photos"] = json.loads(costume["mannequin_photos"])
            costume["model_photos"] = json.loads(costume["model_photos"])
            return costume
        return None

    async def get_costumes_any(self, color_code: str) -> list[dict]:
        """
        Color code bo'yicha barcha kostumlarni topish (is_available ni tekshirmaydi).
        Admin uchun.
        """
        cursor = await self.db.execute(
            "SELECT * FROM costumes WHERE color_code = ?",
            (color_code,)
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            costume = dict(row)
            costume["mannequin_photos"] = json.loads(costume["mannequin_photos"])
            costume["model_photos"] = json.loads(costume["model_photos"])
            result.append(costume)
        return result

    async def update_costume(self, costume_id: int, **kwargs) -> bool:
        """
        Kostumni id bo'yicha yangilash.
        """
        if not kwargs:
            return False

        if "mannequin_photos" in kwargs:
            kwargs["mannequin_photos"] = json.dumps(kwargs["mannequin_photos"])
        if "model_photos" in kwargs:
            kwargs["model_photos"] = json.dumps(kwargs["model_photos"])

        set_clause = ", ".join(f"{key} = ?" for key in kwargs.keys())
        values = list(kwargs.values()) + [costume_id]

        cursor = await self.db.execute(
            f"UPDATE costumes SET {set_clause} WHERE id = ?",
            values
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def delete_costume(self, costume_id: int) -> bool:
        """Kostumni id bo'yicha o'chirish."""
        cursor = await self.db.execute(
            "DELETE FROM costumes WHERE id = ?",
            (costume_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def toggle_costume(self, costume_id: int) -> Optional[bool]:
        """
        Kostum mavjudligini almashtirish (toggle).
        """
        costume = await self.get_costume_by_id(costume_id)
        if not costume:
            return None

        new_status = not costume["is_available"]
        await self.db.execute(
            "UPDATE costumes SET is_available = ? WHERE id = ?",
            (new_status, costume_id)
        )
        await self.db.commit()
        return new_status

    async def list_costumes(self, available_only: bool = False) -> list[dict]:
        """
        Barcha kostumlar ro'yxatini qaytaradi.
        available_only=True bo'lsa, faqat mavjud kostumlar.
        """
        if available_only:
            cursor = await self.db.execute(
                "SELECT * FROM costumes WHERE is_available = 1 ORDER BY created_at DESC"
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM costumes ORDER BY created_at DESC"
            )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            costume = dict(row)
            costume["mannequin_photos"] = json.loads(costume["mannequin_photos"])
            costume["model_photos"] = json.loads(costume["model_photos"])
            result.append(costume)
        return result

    async def get_costume_count(self) -> int:
        """Jami kostumlar sonini qaytaradi."""
        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM costumes")
        row = await cursor.fetchone()
        return row["cnt"]

    async def get_available_color_codes(self) -> list[str]:
        """Barcha mavjud color raqamlarni qaytaradi (catalog uchun)."""
        cursor = await self.db.execute(
            "SELECT color_code, name FROM costumes WHERE is_available = 1 ORDER BY color_code"
        )
        rows = await cursor.fetchall()
        return [(row["color_code"], row["name"]) for row in rows]

    # ═══════════════════════════════════════════════
    # Qidiruv loglari va statistika
    # ═══════════════════════════════════════════════

    async def log_search(self, user_id: int, query: str, color_code: str = "", found: bool = False):
        """Qidiruv so'rovini loglash."""
        await self.db.execute(
            "INSERT INTO search_logs (user_id, query, color_code, found) VALUES (?, ?, ?, ?)",
            (user_id, query, color_code, found)
        )
        await self.db.commit()

    async def get_stats(self) -> dict:
        """Bot statistikasini qaytaradi."""
        stats = {}

        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM users")
        row = await cursor.fetchone()
        stats["total_users"] = row["cnt"]

        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM costumes")
        row = await cursor.fetchone()
        stats["total_costumes"] = row["cnt"]

        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM costumes WHERE is_available = 1")
        row = await cursor.fetchone()
        stats["available_costumes"] = row["cnt"]

        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM search_logs")
        row = await cursor.fetchone()
        stats["total_searches"] = row["cnt"]

        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM search_logs WHERE found = 1")
        row = await cursor.fetchone()
        stats["successful_searches"] = row["cnt"]

        cursor = await self.db.execute(
            "SELECT COUNT(*) as cnt FROM search_logs WHERE DATE(searched_at) = DATE('now')"
        )
        row = await cursor.fetchone()
        stats["today_searches"] = row["cnt"]

        cursor = await self.db.execute(
            """SELECT color_code, COUNT(*) as cnt FROM search_logs 
            WHERE color_code != '' AND found = 1
            GROUP BY color_code ORDER BY cnt DESC LIMIT 5"""
        )
        rows = await cursor.fetchall()
        stats["top_searched"] = [(row["color_code"], row["cnt"]) for row in rows]

        return stats

    # ═══════════════════════════════════════════════
    # Sevimlilar
    # ═══════════════════════════════════════════════

    async def add_favorite(self, user_id: int, costume_id: int) -> bool:
        """Sevimliga qo'shish. Muvaffaqiyatli bo'lsa True."""
        try:
            await self.db.execute(
                "INSERT INTO favorites (user_id, costume_id) VALUES (?, ?)",
                (user_id, costume_id)
            )
            await self.db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def remove_favorite(self, user_id: int, costume_id: int) -> bool:
        """Sevimlilardan o'chirish."""
        cursor = await self.db.execute(
            "DELETE FROM favorites WHERE user_id = ? AND costume_id = ?",
            (user_id, costume_id)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def is_favorite(self, user_id: int, costume_id: int) -> bool:
        """Kostum sevimlilarda bormi?"""
        cursor = await self.db.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND costume_id = ?",
            (user_id, costume_id)
        )
        return await cursor.fetchone() is not None

    async def get_favorites(self, user_id: int) -> list[dict]:
        """Foydalanuvchining sevimli kostumlari."""
        cursor = await self.db.execute(
            """SELECT c.* FROM costumes c
            INNER JOIN favorites f ON c.id = f.costume_id
            WHERE f.user_id = ? AND c.is_available = 1
            ORDER BY f.added_at DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            costume = dict(row)
            costume["mannequin_photos"] = json.loads(costume["mannequin_photos"])
            costume["model_photos"] = json.loads(costume["model_photos"])
            result.append(costume)
        return result

    # ═══════════════════════════════════════════════
    # Oxirgi ko'rilganlar
    # ═══════════════════════════════════════════════

    async def get_recent_searches(self, user_id: int, limit: int = 5) -> list[dict]:
        """
        Foydalanuvchining oxirgi muvaffaqiyatli qidiruvlari.
        Takroriylarni olib tashlaydi.
        """
        cursor = await self.db.execute(
            """SELECT DISTINCT s.color_code, c.name, c.price, MAX(s.searched_at) as last_seen
            FROM search_logs s
            INNER JOIN costumes c ON s.color_code = c.color_code
            WHERE s.user_id = ? AND s.found = 1 AND c.is_available = 1
            GROUP BY s.color_code
            ORDER BY last_seen DESC
            LIMIT ?""",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ═══════════════════════════════════════════════
    # Excel eksport uchun
    # ═══════════════════════════════════════════════

    async def get_all_costumes_for_export(self) -> list[dict]:
        """Barcha kostumlarni eksport uchun qaytaradi."""
        cursor = await self.db.execute(
            "SELECT * FROM costumes ORDER BY color_code"
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            costume = dict(row)
            costume["mannequin_photos_count"] = len(json.loads(costume["mannequin_photos"]))
            costume["model_photos_count"] = len(json.loads(costume["model_photos"]))
            result.append(costume)
        return result