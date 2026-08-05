import logging
from typing import Type, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.services.ingestion.connector_base import DataSourceConnector
from app.services.ingestion.connectors.sbp import SBPConnector
from app.services.ingestion.connectors.psx import PSXConnector
from app.services.ingestion.connectors.pbs import PBSConnector
from app.services.ingestion.connectors.rss import RSSConnector
from app.services.ingestion.connectors.fbr import FBRConnector
from app.services.ingestion.connectors.csv_connector import CSVConnector
from app.services.ingestion.connectors.youtube import YouTubeConnector
from app.services.ingestion.connectors.worldbank import WorldBankConnector
from app.services.ingestion.connectors.commodity import CommodityConnector
from app.services.ingestion.connectors.public_discussion import PublicDiscussionConnector

logger = logging.getLogger("pepr.ingestion")


class IngestionManager:
    CONNECTOR_REGISTRY: Dict[str, Type[DataSourceConnector]] = {
        "sbp": SBPConnector,
        "psx": PSXConnector,
        "pbs": PBSConnector,
        "rss": RSSConnector,
        "public_discussion": PublicDiscussionConnector,
        "gdelt": PublicDiscussionConnector,
        "fbr": FBRConnector,
        "csv_connector": CSVConnector,
        "youtube": YouTubeConnector,
        "worldbank": WorldBankConnector,
        "commodity": CommodityConnector,
    }


    def __init__(self, db: AsyncSession, source_id: str, connector_type: str, config: Dict[str, Any]):
        self.db = db
        self.source_id = source_id
        self.connector_type = connector_type
        if connector_type not in self.CONNECTOR_REGISTRY:
            raise ValueError(f"Unknown connector type: '{connector_type}'. Available: {list(self.CONNECTOR_REGISTRY.keys())}")

        connector_class = self.CONNECTOR_REGISTRY[connector_type]
        # Pass db session into connector so persist() can write to PostgreSQL
        self.connector = connector_class(config=config, db=db)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _fetch_with_retries(self) -> Any:
        return await self.connector.fetch()

    def _apply_data_quality_guardrails(self, records: Any) -> Any:
        if not isinstance(records, list):
            return records
        import math
        clean_records = []
        for r in records:
            if not isinstance(r, dict):
                clean_records.append(r)
                continue
            if "value" in r and r["value"] is not None:
                try:
                    val = float(r["value"])
                    if math.isnan(val) or math.isinf(val) or abs(val) > 1e15:
                        logger.warning(f"Data quality guardrail dropped invalid observation value: {r['value']}")
                        continue
                except (ValueError, TypeError):
                    continue
            clean_records.append(r)
        return clean_records

    async def run_ingestion(self) -> Dict[str, Any]:
        """
        Executes the full ingestion pipeline: Fetch -> Normalize -> Validate -> Persist.
        Returns a result dict with status, records_processed, and metadata.
        """
        logger.info(f"Starting ingestion for source_id={self.source_id}")
        try:
            # 1. Fetch with retry logic
            raw_data = await self._fetch_with_retries()
            metadata = self.connector.get_metadata()

            # 2. Normalize
            normalized = self.connector.normalize(raw_data)
            logger.info(f"[{self.source_id}] Normalized {len(normalized)} records")

            # 3. Validate & apply data quality guardrails
            if not self.connector.validate(normalized):
                raise ValueError("Validation failed for normalized data")

            normalized = self._apply_data_quality_guardrails(normalized)

            if len(normalized) == 0:
                logger.warning(
                    f"[{self.source_id}] No records returned from external source. "
                    "Source may be temporarily unavailable. Skipping persist."
                )
                return {
                    "status": "success",
                    "records_processed": 0,
                    "source_id": self.source_id,
                    "metadata": self.connector.get_metadata(),
                }

            # 4. Persist to PostgreSQL via connector's persist() method
            await self.connector.persist(normalized)


            # 5. Run automated post-ingestion NLP Analysis
            try:
                from app.services.analysis.post_ingestion import run_post_ingestion_analysis
                await run_post_ingestion_analysis(self.db, self.connector_type)
            except Exception as analysis_err:
                logger.warning(f"Post-ingestion analysis failed: {analysis_err}")

            return {
                "status": "success",
                "records_processed": len(normalized),
                "source_id": self.source_id,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(
                f"Ingestion failed for source_id={self.source_id}: {str(e)}",
                exc_info=True
            )
            return {
                "status": "failed",
                "source_id": self.source_id,
                "error": str(e),
            }
