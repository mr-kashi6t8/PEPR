import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.services.ingestion.connectors.youtube import YouTubeConnector

async def test():
    print("Testing YouTubeConnector with real YouTube video IDs & channel feeds...")
    config = {
        "channel_ids": [
            "UC_gUM8rL-LzyuZCEz5Edafw" # Geo News
        ],
        "video_ids": [
            "jNQXAC9IVRw"
        ],
        "source_name": "YouTube Economy Talks"
    }
    
    async with AsyncSessionLocal() as db:
        connector = YouTubeConnector(db=db, config=config)
        connector.validate_configuration()
        raw = await connector.fetch()
        print(f"Raw Transcripts Fetched: {len(raw)}")
        normalized = connector.normalize(raw)
        print(f"Normalized Items: {len(normalized)}")
        if normalized:
            await connector.persist(normalized)
            print("Successfully persisted YouTube transcripts to database!")

if __name__ == "__main__":
    asyncio.run(test())
