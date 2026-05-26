import sqlite3
import shutil
import os

DB_PATH = "costume_bot.db"
BACKUP_PATH = "costume_bot.db.bak"

def migrate():
    print(f"Backing up database to {BACKUP_PATH}...")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Disable foreign keys temporarily
    cursor.execute("PRAGMA foreign_keys=OFF")
    
    print("Creating costumes_new table without UNIQUE constraint...")
    cursor.execute("""
        CREATE TABLE costumes_new (
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
    """)
    
    print("Copying data from costumes to costumes_new...")
    cursor.execute("INSERT INTO costumes_new SELECT * FROM costumes;")
    
    print("Creating favorites_new table to preserve constraints...")
    cursor.execute("""
        CREATE TABLE favorites_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            costume_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (costume_id) REFERENCES costumes(id) ON DELETE CASCADE,
            UNIQUE(user_id, costume_id)
        );
    """)
    cursor.execute("INSERT INTO favorites_new SELECT * FROM favorites;")
    
    print("Dropping old tables...")
    cursor.execute("DROP TABLE favorites;")
    cursor.execute("DROP TABLE costumes;")
    
    print("Renaming new tables to original names...")
    cursor.execute("ALTER TABLE costumes_new RENAME TO costumes;")
    cursor.execute("ALTER TABLE favorites_new RENAME TO favorites;")
    
    print("Recreating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_costumes_color ON costumes(color_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);")
    
    print("Enabling foreign keys...")
    cursor.execute("PRAGMA foreign_keys=ON")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
