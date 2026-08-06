import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.services.analysis.post_ingestion import run_post_ingestion_analysis

async def test_pipeline():
    async with AsyncSessionLocal() as db:
        print("=== SIMULATING M1 INGESTION COMPLETE TRIGGER FOR M2 ENGINE ===")
        await run_post_ingestion_analysis(db=db, source_type="macro")
        print("\n[✓] Post-Ingestion Pipeline (M1 Ingestion -> M2 Statistical Engine) completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
