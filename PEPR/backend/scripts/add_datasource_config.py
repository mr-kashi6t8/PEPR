"""Add a DataSourceConfig row for an existing DataSource.

Usage:
  python add_datasource_config.py <source_id_or_name> '<credentials_json>' '<parsing_rules_json>'

Example:
  python add_datasource_config.py youtube_talkshows '{"channel_ids": ["UC...", "UC..."]}' '{}'
"""
import sys
import json
import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.models.ingestion import DataSource, DataSourceConfig

async def main():
    if len(sys.argv) < 3:
        print("Usage: python add_datasource_config.py <source_id_or_name> '<credentials_json>' ['<parsing_rules_json>']")
        return

    identifier = sys.argv[1]
    creds_raw = sys.argv[2]
    parsing_raw = sys.argv[3] if len(sys.argv) > 3 else "{}"

    try:
        credentials = json.loads(creds_raw)
    except Exception as e:
        print("Invalid credentials JSON:", e)
        return

    try:
        parsing_rules = json.loads(parsing_raw)
    except Exception as e:
        print("Invalid parsing_rules JSON:", e)
        return

    async with AsyncSessionLocal() as db:
        # Try lookup by UUID (id) first
        ds = None
        try:
            from sqlalchemy import select
            stmt = select(DataSource).where(DataSource.id == identifier)
            res = await db.execute(stmt)
            ds = res.scalars().first()
        except Exception:
            ds = None

        if not ds:
            # fallback to name
            from sqlalchemy import select
            stmt = select(DataSource).where(DataSource.name == identifier)
            res = await db.execute(stmt)
            ds = res.scalars().first()

        if not ds:
            print(f"DataSource not found for identifier '{identifier}'")
            return

        cfg = DataSourceConfig(source_id=ds.id, credentials=credentials, parsing_rules=parsing_rules)
        db.add(cfg)
        await db.commit()
        await db.refresh(cfg)
        print(f"Created DataSourceConfig id={cfg.id} for DataSource id={ds.id} name={ds.name}")

if __name__ == '__main__':
    asyncio.run(main())
