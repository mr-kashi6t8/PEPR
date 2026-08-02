import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.services.ingestion.connectors.fbr import FBRConnector

async def test():
    print("Testing FBRConnector with live https://www.fbr.gov.pk/ ...")
    config = {"url": "https://www.fbr.gov.pk/"}
    
    async with AsyncSessionLocal() as db:
        connector = FBRConnector(db=db, config=config)
        connector.validate_configuration()
        raw = await connector.fetch()
        print(f"Raw HTML bytes fetched: {len(raw)}")
        normalized = connector.normalize(raw)
        print(f"Normalized FBR Items: {len(normalized)}")
        if normalized:
            for item in normalized[:3]:
                print(f"  • {item['indicator_name']}: {item.get('value_extracted') or item.get('collection_amount')}")
            await connector.persist(normalized)
            print("Successfully persisted FBR live revenue records to database!")

if __name__ == "__main__":
    asyncio.run(test())
