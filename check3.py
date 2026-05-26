import sqlite3
conn = sqlite3.connect('costume_bot.db')
c = conn.cursor()
c.execute("SELECT color_code, is_available FROM costumes LIMIT 5")
for r in c.fetchall():
    print(r)
conn.close()