import asyncio
from sqlalchemy import delete, select
from app.infrastructure.database import AsyncSessionLocal
from app.models.ingestion import IngestionRun

async def main():
    async with AsyncSessionLocal() as db:
        # Delete old failed runs from yesterday that clutter the UI
        stmt = delete(IngestionRun).where(IngestionRun.status == "FAILED", IngestionRun.records_fetched == 0)
        res = await db.execute(stmt)
        await db.commit()
        print(f"Purged {res.rowcount} old failed/abandoned job run logs from database!")

if __name__ == "__main__":
    asyncio.run(main())
