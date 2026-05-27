import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from sdpj.infrastructure.database.user_db.session import get_session


async def main():
    async for s in get_session():
        r = await s.execute(
            text("SELECT resource_id, content FROM private_configs WHERE resource_id = 4")
        )
        row = r.fetchone()
        if row:
            print(f"ID={row[0]}")
            print(row[1] if row[1] else "EMPTY")
        else:
            print("Not found")


if __name__ == "__main__":
    asyncio.run(main())
