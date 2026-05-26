import asyncio
from database import Database

async def test():
    db = Database('costume_bot.db')
    await db.connect()
    c = await db.get_costume('79/643')
    print('Costume:', c)
    await db.close()

if __name__ == "__main__":
    asyncio.run(test())
