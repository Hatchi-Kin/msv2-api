import asyncio
import asyncpg
async def test_db():
    try:
        conn = await asyncpg.connect('postgresql://adama:commander@localhost:5432/glasgow_db', timeout=5)
        print('Connection successful!')
        await conn.close()
    except Exception as e:
        print(f'Connection failed: {e}')

asyncio.run(test_db())
