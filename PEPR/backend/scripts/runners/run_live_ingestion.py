import asyncio
import json
from app.infrastructure.database import AsyncSessionLocal
from app.services.ingestion.manager import IngestionManager

async def main():
    print("Starting live data ingestion from all configured sources in sources.json...")
    async with AsyncSessionLocal() as db:
        with open("sources.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            sources = data.get("sources", [])
        
        for source_cfg in sources:
            source_id = source_cfg.get("id") or source_cfg.get("name")
            connector_type = source_cfg.get("type")
            config = source_cfg.get("config", {})
            
            print(f"\n---> Running connector '{connector_type}' for source '{source_id}'...")
            try:
                mgr = IngestionManager(db=db, source_id=str(source_id), connector_type=connector_type, config=config)
                result = await mgr.run_ingestion()
                print(f"Result: {result}")
            except Exception as e:
                print(f"Failed to run connector '{connector_type}': {e}")

if __name__ == "__main__":
    asyncio.run(main())
