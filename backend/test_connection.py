import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def test():
    db_url = os.environ.get("DATABASE_URL")
    print(f"Connecting to: {db_url[:60]}...")
    
    try:
        conn = await asyncpg.connect(db_url)
        count = await conn.fetchval("SELECT COUNT(*) FROM maintenance_tasks")
        print(f"✓ Connected! Found {count} tasks.")
        await conn.close()
    except Exception as e:
        print(f"✗ Error: {e}")

asyncio.run(test())