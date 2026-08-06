import asyncio
from sqlalchemy import select, update, delete, func
from app.infrastructure.database import AsyncSessionLocal
from app.models.ingestion import DataSource, IngestionJob, IngestionRun
from app.models.news import NewsArticle
from datetime import datetime, timezone, timedelta

async def cleanup():
    async with AsyncSessionLocal() as db:
        print("--- 1. Cleaning up stuck 'RUNNING' jobs older than 10 minutes ---")
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
        stmt_stuck = (
            update(IngestionRun)
            .where(IngestionRun.status == "RUNNING", IngestionRun.created_at < cutoff)
            .values(status="FAILED", error_message="Job timed out or process was interrupted")
        )
        res_stuck = await db.execute(stmt_stuck)
        print(f"Updated {res_stuck.rowcount} stuck RUNNING jobs to FAILED.")

        print("\n--- 2. Inspecting Data Sources ---")
        stmt_ds = select(DataSource)
        res_ds = await db.execute(stmt_ds)
        sources = res_ds.scalars().all()
        for s in sources:
            print(f"ID: {s.id} | Name: {s.name} | Type: {s.source_type} | Base URL: {s.base_url}")

        print("\n--- 3. Merging/Deduplicating duplicate DataSources ---")
        # Canonical names mapping
        name_map = {
            "Pakistan Bureau of Statistics (PBS)": "Pakistan Bureau of Statistics",
            "State Bank of Pakistan (SBP)": "State Bank of Pakistan",
            "Pakistan Stock Exchange (PSX)": "Pakistan Stock Exchange",
            "YouTube Economy Talks": "YouTube Economy Shows",
        }

        for s in sources:
            if s.name in name_map:
                canonical_name = name_map[s.name]
                # Find canonical source
                stmt_can = select(DataSource).where(DataSource.name == canonical_name)
                res_can = await db.execute(stmt_can)
                can_source = res_can.scalars().first()
                if can_source and can_source.id != s.id:
                    # Move jobs & news articles to canonical source
                    stmt_move_jobs = update(IngestionJob).where(IngestionJob.source_id == s.id).values(source_id=can_source.id)
                    await db.execute(stmt_move_jobs)
                    
                    stmt_move_news = update(NewsArticle).where(NewsArticle.source_id == s.id).values(source_id=can_source.id)
                    await db.execute(stmt_move_news)
                    
                    # Delete duplicate data source
                    stmt_del = delete(DataSource).where(DataSource.id == s.id)
                    await db.execute(stmt_del)
                    print(f"Merged duplicate source '{s.name}' -> '{canonical_name}'")

        await db.commit()
        print("\nCleanup completed successfully!")

if __name__ == "__main__":
    asyncio.run(cleanup())
