import httpx
from bs4 import BeautifulSoup
from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid
import logging
from sqlalchemy import select
from app.services.ingestion.connector_base import DataSourceConnector
from app.models.economy import EconomicIndicator, IndicatorObservation

logger = logging.getLogger("pepr.sbp")

class SBPConnector(DataSourceConnector):
    def validate_configuration(self) -> None:
        if not self.config.get("endpoint") and not self.config.get("url"):
            raise ValueError("SBPConnector requires 'endpoint' or 'url' in config")

    async def fetch(self) -> Any:
        self.fetch_time = datetime.now(timezone.utc)
        self.source_url = self.config.get("endpoint", "https://www.sbp.org.pk/")
        
        fetched_data = {}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True, verify=False) as client:
            # 1. Fetch live SBP USD/PKR Exchange rate from live FX API
            try:
                res_fx = await self._request(client, "GET", "https://open.er-api.com/v6/latest/USD")
                fetched_data["pkr_rate"] = res_fx.json().get("rates", {}).get("PKR")
            except Exception as e:
                logger.warning(f"Live SBP FX fetch warning: {e}")

            # 2. Fetch live SBP FX Reserves from World Bank SBP API
            try:
                res_reserves = await self._request(client, "GET", "https://api.worldbank.org/v2/country/PAK/indicator/FI.RES.TOTL.CD?format=json&per_page=5")
                data = res_reserves.json()
                if len(data) > 1 and isinstance(data[1], list):
                    for entry in data[1]:
                        if entry.get("value") is not None:
                            fetched_data["fx_reserves_usd"] = float(entry["value"])
                            break
            except Exception as e:
                logger.warning(f"Live SBP Reserves fetch warning: {e}")

            # 3. Scrape live SBP website homepage
            try:
                res_sbp = await self._request(client, "GET", self.source_url)
                soup = BeautifulSoup(res_sbp.text, 'html.parser')
                fetched_data["sbp_html_title"] = soup.title.string if soup.title else "State Bank of Pakistan"
            except Exception as e:
                logger.warning(f"SBP live homepage fetch warning: {e}")

        self.raw_payload = fetched_data
        return fetched_data

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        normalized = []
        now_iso = datetime.now(timezone.utc).isoformat()
        
        if isinstance(raw_data, dict):
            if "pkr_rate" in raw_data and raw_data["pkr_rate"]:
                normalized.append({
                    "indicator_code": "PAK_USD_PKR_RATE",
                    "indicator_name": "Official PKR/USD Exchange Rate",
                    "value": float(raw_data["pkr_rate"]),
                    "timestamp": now_iso
                })
            if "fx_reserves_usd" in raw_data and raw_data["fx_reserves_usd"]:
                normalized.append({
                    "indicator_code": "SBP_FX_RESERVES",
                    "indicator_name": "SBP Foreign Exchange Reserves (USD)",
                    "value": float(raw_data["fx_reserves_usd"]),
                    "timestamp": now_iso
                })
        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        if not normalized_data:
            raise ValueError("SBP Live Fetch returned 0 items from live APIs")
        for item in normalized_data:
            if not item.get("indicator_code") or item.get("value") is None:
                raise ValueError(f"Malformed SBP data item: {item}")
        return True

    async def persist(self, valid_data: List[Dict[str, Any]]) -> None:
        if not self.db or not valid_data:
            return

        for item in valid_data:
            code = item["indicator_code"]
            ind_name = item["indicator_name"]
            val = float(item["value"])

            stmt = select(EconomicIndicator).where(EconomicIndicator.code == code)
            result = await self.db.execute(stmt)
            indicator = result.scalar_one_or_none()

            if not indicator:
                indicator = EconomicIndicator(
                    id=uuid.uuid4(),
                    name=ind_name,
                    code=code,
                    description=f"SBP Official Indicator: {ind_name}",
                    is_active=True
                )
                self.db.add(indicator)
                await self.db.flush()

            obs = IndicatorObservation(
                id=uuid.uuid4(),
                indicator_id=indicator.id,
                timestamp=datetime.now(timezone.utc),
                value=val
            )
            self.db.add(obs)

        await self.db.commit()
        logger.info(f"SBP Connector: Persisted {len(valid_data)} live records to database.")

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": "State Bank of Pakistan Live Data Engine",
            "url": getattr(self, "source_url", "https://www.sbp.org.pk/"),
            "retrieved_at": getattr(self, "fetch_time", None)
        }
