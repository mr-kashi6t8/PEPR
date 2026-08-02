import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.api.v1.endpoints.ingestion import list_data_sources, list_ingestion_jobs

async def main():
    async with AsyncSessionLocal() as db:
        print("=== DATA SOURCES METRICS ===")
        sources = await list_data_sources(db=db)
        for s in sources:
            print(f"[{s['name']}] Last Run: {s['last_run']} | Ingested: {s['records_ingested']} | Error Rate: {s['error_rate']}%")

        print("\n=== RECENT INGESTION JOBS ===")
        jobs = await list_ingestion_jobs(db=db)
        for j in jobs:
            print(f"[{j['source_name']}] Status: {j['status']} | Processed: {j['records_processed']} | Started: {j['started_at']}")

if __name__ == "__main__":
    asyncio.run(main())
