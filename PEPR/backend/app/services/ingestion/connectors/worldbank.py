import httpx
from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from app.services.ingestion.connector_base import DataSourceConnector
from app.models.economy import EconomicIndicator, IndicatorObservation

class WorldBankConnector(DataSourceConnector):
    """
    World Bank Open Data Connector for Pakistan.
    Fetches real official macroeconomic time series for Pakistan directly from World Bank Open REST API.
    """
    INDICATORS_MAP = {
        "FP.CPI.TOTL.ZG": {"code": "PAK_CPI_YOY", "name": "Consumer Price Index (CPI Inflation %)", "unit": "% YoY"},
        "NY.GDP.MKTP.KD.ZG": {"code": "WB_GDP_GROWTH", "name": "Real GDP Growth Rate", "unit": "% Annual"},
        "FI.RES.TOTL.CD": {"code": "SBP_FX_RESERVES", "name": "Total Liquid FX Reserves (USD)", "unit": "USD"},
        "BN.CAB.XOKA.CD": {"code": "PAK_CURRENT_ACCOUNT", "name": "Current Account Balance (USD)", "unit": "USD"},
        "NE.TRD.GNFS.ZS": {"code": "PAK_TRADE_PCT_GDP", "name": "Trade Volume (% of GDP)", "unit": "% of GDP"},
        "PA.NUS.FCRF": {"code": "PAK_USD_PKR_RATE", "name": "Official PKR/USD Exchange Rate", "unit": "PKR per USD"},
        "GC.TAX.TOTL.GD.ZS": {"code": "FBR_TAX_PCT_GDP", "name": "Tax Revenue (% of GDP)", "unit": "% of GDP"},
        "SL.UEM.TOTL.ZS": {"code": "PAK_UNEMPLOYMENT_RATE", "name": "Unemployment Rate (% of Labor)", "unit": "%"}
    }

    def validate_configuration(self) -> None:
        indicator_ids = self.config.get("indicator_ids")
        if indicator_ids is not None and not isinstance(indicator_ids, list):
            raise ValueError("WorldBankConnector expects 'indicator_ids' to be a list when provided")

    async def fetch(self) -> Any:
        self.fetch_time = datetime.now(timezone.utc)
        results = []
        indicator_ids = self.config.get("indicator_ids") or list(self.INDICATORS_MAP.keys())
        async with httpx.AsyncClient(timeout=30.0) as client:
            for ind_id in indicator_ids:
                url = f"https://api.worldbank.org/v2/country/PAK/indicator/{ind_id}?format=json&per_page=60"
                try:
                    res = await client.get(url)
                    if res.status_code == 200:
                        data = res.json()
                        if len(data) > 1 and isinstance(data[1], list):
                            results.extend(data[1])
                except Exception:
                    continue
        self.raw_payload = results
        return results

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        normalized = []
        for item in raw_data:
            ind_info = item.get("indicator", {})
            ind_id = ind_info.get("id")
            val = item.get("value")
            year_str = item.get("date")
            
            if ind_id in self.INDICATORS_MAP and val is not None and year_str:
                meta = self.INDICATORS_MAP[ind_id]
                try:
                    dt = datetime(int(year_str), 1, 1, tzinfo=timezone.utc)
                except ValueError:
                    dt = datetime.now(timezone.utc)
                    
                normalized.append({
                    "indicator_code": meta["code"],
                    "indicator_name": meta["name"],
                    "unit": meta["unit"],
                    "value": float(val),
                    "timestamp": dt
                })
        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        return len(normalized_data) > 0

    async def persist(self, valid_data: List[Dict[str, Any]]) -> None:
        if not self.db or not valid_data:
            return
            
        for item in valid_data:
            code = item["indicator_code"]
            name = item["indicator_name"]
            val = item["value"]
            ts = item["timestamp"]
            
            stmt = select(EconomicIndicator).where(EconomicIndicator.code == code)
            result = await self.db.execute(stmt)
            indicator = result.scalar_one_or_none()
            
            if not indicator:
                indicator = EconomicIndicator(
                    id=uuid.uuid4(),
                    name=name,
                    code=code,
                    description=f"Official World Bank Series: {name}",
                    is_active=True
                )
                self.db.add(indicator)
                await self.db.flush()
                
            obs = IndicatorObservation(
                id=uuid.uuid4(),
                indicator_id=indicator.id,
                timestamp=ts,
                value=val
            )
            self.db.add(obs)
            
        await self.db.commit()

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source_agency": "World Bank Open Data API",
            "country": "Pakistan (PAK)",
            "retrieval_timestamp": getattr(self, "fetch_time", None)
        }
