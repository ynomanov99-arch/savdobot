import sqlite3
conn=sqlite3.connect('costume_bot.db')
c=conn.cursor()
c.execute('SELECT color_code FROM costumes LIMIT 20')
for r in c.fetchall():
    print(repr(r[0]))
conn.close()