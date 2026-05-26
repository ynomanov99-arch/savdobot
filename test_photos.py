import sqlite3

conn = sqlite3.connect('costume_bot.db')
cursor = conn.cursor()
cursor.execute('SELECT color_code, mannequin_photos, model_photos FROM costumes WHERE color_code = "23/33";')
print("23/33:", cursor.fetchone())

cursor.execute('SELECT color_code, mannequin_photos, model_photos FROM costumes WHERE mannequin_photos != "[]" OR model_photos != "[]" LIMIT 5;')
print("Has photos:", cursor.fetchall())
