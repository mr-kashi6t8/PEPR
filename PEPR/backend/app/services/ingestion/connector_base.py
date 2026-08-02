from abc import ABC, abstractmethod
import asyncio
import random
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession


class DataSourceConnector(ABC):
    """
    Abstract Base Class for all Data Ingestion Connectors.
    Each connector must be independently testable and implement these methods.
    The db session is injected by the IngestionManager so connectors can persist.
    """

    def __init__(self, config: Dict[str, Any], db: Optional[AsyncSession] = None):
        self.config = config
        self.db = db  # AsyncSession injected by manager for DB persistence
        self.validate_configuration()

    async def _polite_sleep(self) -> None:
        min_delay = float(self.config.get("min_delay_seconds", 0.75))
        max_delay = float(self.config.get("max_delay_seconds", max(min_delay, 2.5)))
        await asyncio.sleep(random.uniform(min_delay, max_delay))

    async def _request(self, client: httpx.AsyncClient, method: str, url: str, **kwargs: Any) -> httpx.Response:
        retries = int(self.config.get("request_retries", 3))
        last_error: Optional[Exception] = None

        for attempt in range(1, retries + 1):
            try:
                await self._polite_sleep()
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                if attempt >= retries:
                    raise
                await asyncio.sleep(min(5.0, attempt * 1.5))

        assert last_error is not None
        raise last_error

    @abstractmethod
    def validate_configuration(self) -> None:
        """Validates that the provided configuration is correct for this connector."""
        pass

    @abstractmethod
    async def fetch(self) -> Any:
        """Fetches raw data from the external source."""
        pass

    @abstractmethod
    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Normalizes the raw data into common internal schemas."""
        pass

    @abstractmethod
    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        """Validates the normalized data against required schemas."""
        pass

    @abstractmethod
    async def persist(self, valid_data: List[Dict[str, Any]]) -> None:
        """Persists the validated data into the PostgreSQL database."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns metadata about the connector run (e.g., source URLs, timestamps)."""
        pass
