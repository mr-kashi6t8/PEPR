import httpx
from bs4 import BeautifulSoup
from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid
import logging
from sqlalchemy import select
from app.services.ingestion.connector_base import DataSourceConnector
from app.models.economy import EconomicIndicator, IndicatorObservation

logger = logging.getLogger("pepr.psx")

class PSXConnector(DataSourceConnector):
    def validate_configuration(self) -> None:
        if not self.config.get("endpoint") and not self.config.get("url"):
            raise ValueError("PSXConnector requires 'endpoint' or 'url' in config")

    async def fetch(self) -> Any:
        self.fetch_time = datetime.now(timezone.utc)
        self.source_url = self.config.get("endpoint", "https://dps.psx.com.pk/")
        
        fetched = {}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True, verify=False) as client:
            # 1. Scrape live PSX data portal summary
            try:
                res_psx = await self._request(client, "GET", "https://dps.psx.com.pk/summary")
                soup = BeautifulSoup(res_psx.text, 'html.parser')
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:
                        cols = row.find_all(['td', 'th'])
                        if len(cols) >= 2:
                            symbol = cols[0].get_text(strip=True)
                            val_str = cols[1].get_text(strip=True)
                            if any(char.isdigit() for char in val_str):
                                try:
                                    val = float(val_str.replace(",", ""))
                                    fetched["psx_index_val"] = val
                                    fetched["psx_symbol"] = symbol
                                    break
                                except ValueError:
                                    pass
            except Exception as e:
                logger.warning(f"PSX live portal fetch warning: {e}")

            # 2. Fetch live Pakistan Trade Volume (% of GDP) from World Bank Open API
            try:
                res_trade = await self._request(client, "GET", "https://api.worldbank.org/v2/country/PAK/indicator/NE.TRD.GNFS.ZS?format=json&per_page=5")
                data = res_trade.json()
                if len(data) > 1 and isinstance(data[1], list):
                    for item in data[1]:
                        if item.get("value") is not None:
                            fetched["trade_pct_gdp"] = float(item["value"])
                            break
            except Exception as e:
                logger.warning(f"WorldBank PSX Trade fetch error: {e}")

        self.raw_payload = fetched
        return fetched

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        normalized = []
        now_iso = datetime.now(timezone.utc).isoformat()
        
        if isinstance(raw_data, dict):
            if "psx_index_val" in raw_data and raw_data["psx_index_val"] is not None:
                normalized.append({
                    "indicator_code": "PSX_KSE100",
                    "indicator_name": f"PSX Market - {raw_data.get('psx_symbol', 'KSE100')}",
                    "value": float(raw_data["psx_index_val"]),
                    "timestamp": now_iso
                })
            if "trade_pct_gdp" in raw_data and raw_data["trade_pct_gdp"] is not None:
                normalized.append({
                    "indicator_code": "PAK_TRADE_PCT_GDP",
                    "indicator_name": "Trade Volume (% of GDP)",
                    "value": float(raw_data["trade_pct_gdp"]),
                    "timestamp": now_iso
                })

        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        if not normalized_data:
            raise ValueError("PSX Live Fetch returned 0 records from live market APIs")
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
                    description=f"PSX Market Indicator: {ind_name}",
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
        logger.info(f"PSX Connector: Persisted {len(valid_data)} live records to database.")

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": "Pakistan Stock Exchange Live Data Engine",
            "url": getattr(self, "source_url", "https://dps.psx.com.pk/"),
            "retrieved_at": getattr(self, "fetch_time", None)
        }
