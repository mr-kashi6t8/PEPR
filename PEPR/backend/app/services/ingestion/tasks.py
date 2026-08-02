from celery import shared_task
from typing import Dict, Any
from app.services.ingestion.manager import IngestionManager
import logging
import asyncio

logger = logging.getLogger("pepr.ingestion")

@shared_task(name="app.services.ingestion.tasks.run_ingestion_task")
def run_ingestion_task(source_id: str, connector_type: str, config: Dict[str, Any]):
    """
    Background task to run ingestion.
    Note: Asyncio event loop is required here since manager uses async/await.
    """
    logger.info(f"Starting scheduled ingestion for {source_id}")
    # In a real app we'd pass a real db session
    # For now this is just a structural stub to demonstrate the celery beat schedule
    from app.infrastructure.database import async_session_maker
    
    async def _run():
        async with async_session_maker() as db:
            manager = IngestionManager(db=db, source_id=source_id, connector_type=connector_type, config=config)
            result = await manager.run_ingestion()
            
            # Continuous Aggregation Trigger:
            # If successful, kick off the analysis and aggregation pipeline
            if result.get("status") == "success":
                from app.services.analysis.tasks import trigger_continuous_aggregation
                # Simulate passing recent data down the chain
                trigger_continuous_aggregation.delay(source_id)
                
            return result
            
    return asyncio.run(_run())
