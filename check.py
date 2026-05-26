import sqlite3
conn=sqlite3.connect('costume_bot.db')
c=conn.cursor()
c.execute("SELECT * FROM costumes WHERE color_code='23/33'")
print(c.fetchone())
conn.close()