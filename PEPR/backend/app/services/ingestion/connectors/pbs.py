import httpx
from bs4 import BeautifulSoup
from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid
import logging
from sqlalchemy import select
from app.services.ingestion.connector_base import DataSourceConnector
from app.models.economy import EconomicIndicator, IndicatorObservation

logger = logging.getLogger("pepr.pbs")

class PBSConnector(DataSourceConnector):
    def validate_configuration(self) -> None:
        if not self.config.get("url") and not self.config.get("endpoint"):
            raise ValueError("PBSConnector requires 'url' or 'endpoint' in config")

    async def fetch(self) -> Any:
        self.fetch_time = datetime.now(timezone.utc)
        self.source_url = self.config.get("url", "https://www.pbs.gov.pk/")
        
        fetched = {}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True, verify=False) as client:
            # 1. Fetch live PBS Consumer Price Index (CPI) from World Bank Official PBS Series API
            try:
                wb_url = "https://api.worldbank.org/v2/country/PAK/indicator/FP.CPI.TOTL.ZG?format=json&per_page=5"
                res_cpi = await self._request(client, "GET", wb_url)
                data = res_cpi.json()
                if len(data) > 1 and isinstance(data[1], list):
                    for item in data[1]:
                        if item.get("value") is not None:
                            fetched["cpi_yoy"] = float(item["value"])
                            break
            except Exception as e:
                logger.warning(f"Live PBS CPI fetch error: {e}")

            # 2. Scrape live PBS website homepage
            try:
                res_pbs = await self._request(client, "GET", self.source_url)
                soup = BeautifulSoup(res_pbs.text, 'html.parser')
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:
                        cols = row.find_all(['td', 'th'])
                        if len(cols) >= 2:
                            t0 = cols[0].get_text(strip=True)
                            t1 = cols[1].get_text(strip=True)
                            if any(char.isdigit() for char in t1):
                                try:
                                    val = float(t1.replace(",", "").replace("%", ""))
                                    fetched["scraped_cpi"] = val
                                    fetched["scraped_name"] = t0[:50]
                                    break
                                except ValueError:
                                    pass
            except Exception as e:
                logger.warning(f"PBS live homepage scraping warning: {e}")

        self.raw_payload = fetched
        return fetched

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        normalized = []
        now_iso = datetime.now(timezone.utc).isoformat()
        
        if isinstance(raw_data, dict):
            if "cpi_yoy" in raw_data and raw_data["cpi_yoy"] is not None:
                normalized.append({
                    "indicator_code": "PAK_CPI_YOY",
                    "indicator_name": "Consumer Price Index (CPI YoY %)",
                    "value": float(raw_data["cpi_yoy"]),
                    "timestamp": now_iso
                })
            if "scraped_cpi" in raw_data and raw_data["scraped_cpi"] is not None:
                normalized.append({
                    "indicator_code": "PBS_LIVE_CPI",
                    "indicator_name": f"PBS Live - {raw_data.get('scraped_name', 'CPI Index')}",
                    "value": float(raw_data["scraped_cpi"]),
                    "timestamp": now_iso
                })

        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        if not normalized_data:
            raise ValueError("PBS Live Fetch returned 0 records from PBS live sources")
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
                    description="Pakistan Bureau of Statistics Inflation Index",
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
        logger.info(f"PBS Connector: Persisted {len(valid_data)} live records to database.")

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": "Pakistan Bureau of Statistics Live Data Engine",
            "url": getattr(self, "source_url", "https://www.pbs.gov.pk/"),
            "retrieved_at": getattr(self, "fetch_time", None)
        }
