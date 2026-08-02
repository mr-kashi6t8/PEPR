import csv
import io
import httpx
from typing import Any, Dict, List
from datetime import datetime, timezone

from app.services.ingestion.connector_base import DataSourceConnector

class CSVConnector(DataSourceConnector):
    """
    Generic CSV Connector for the Ingestion Engine.
    Can ingest structured comma-separated data from a remote URL or local file path.
    """
    def validate_configuration(self) -> None:
        if "csv_url" not in self.config and "file_path" not in self.config:
            raise ValueError("CSVConnector requires either 'csv_url' or 'file_path' in configuration.")

    async def fetch(self) -> Any:
        if "csv_url" in self.config:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.config["csv_url"])
                response.raise_for_status()
                return response.text
        else:
            with open(self.config["file_path"], 'r', encoding='utf-8') as f:
                return f.read()

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        # Use Python's built-in csv module to safely parse raw string data
        normalized = []
        
        # Treat raw_data string as a file object
        f = io.StringIO(raw_data)
        reader = csv.DictReader(f)
        
        for row in reader:
            # We inject ingestion metadata directly into the normalized row
            row_data = dict(row)
            row_data["_ingestion_source"] = self.config.get("csv_url", self.config.get("file_path"))
            row_data["_retrieved_at"] = datetime.now(timezone.utc).isoformat()
            normalized.append(row_data)
            
        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        # A valid CSV extraction must yield at least one row, and rows must be dicts
        if not normalized_data:
            return False
        return all(isinstance(row, dict) for row in normalized_data)

    async def persist(self, valid_data: List[Dict[str, Any]]) -> None:
        if not self.db or not valid_data:
            return
            
        from sqlalchemy import select
        from app.models.economy import EconomicIndicator, IndicatorObservation
        import uuid
        
        for item in valid_data:
            code = item.get("indicator_code") or item.get("code") or item.get("indicator")
            val = item.get("value") or item.get("val")
            ts_str = item.get("timestamp") or item.get("date") or item.get("_retrieved_at")
            
            if not code or val is None:
                continue
                
            try:
                val_float = float(val)
            except (ValueError, TypeError):
                continue
                
            if isinstance(ts_str, str):
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except ValueError:
                    ts = datetime.now(timezone.utc)
            elif isinstance(ts_str, datetime):
                ts = ts_str
            else:
                ts = datetime.now(timezone.utc)
                
            stmt = select(EconomicIndicator).where(EconomicIndicator.code == code)
            result = await self.db.execute(stmt)
            indicator = result.scalar_one_or_none()
            
            if not indicator:
                indicator = EconomicIndicator(
                    id=uuid.uuid4(),
                    name=item.get("name") or code,
                    code=code,
                    description=f"CSV Ingested Indicator {code}",
                    is_active=True
                )
                self.db.add(indicator)
                await self.db.flush()
                
            obs = IndicatorObservation(
                id=uuid.uuid4(),
                indicator_id=indicator.id,
                timestamp=ts,
                value=val_float
            )
            self.db.add(obs)
            
        await self.db.commit()

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": "Generic CSV Connector",
            "path": self.config.get("csv_url", self.config.get("file_path")),
            "type": "remote" if "csv_url" in self.config else "local"
        }

