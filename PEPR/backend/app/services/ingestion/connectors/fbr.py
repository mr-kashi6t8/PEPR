from bs4 import BeautifulSoup
import httpx
from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid
import re
import logging
from sqlalchemy import select
from app.services.ingestion.connector_base import DataSourceConnector
from app.models.economy import EconomicIndicator, IndicatorObservation, IndicatorMetadata

logger = logging.getLogger("pepr.fbr")


class FBRConnector(DataSourceConnector):
    """
    Web & API Connector for Federal Board of Revenue (FBR) Pakistan & World Bank Tax Data.
    Fetches live tax revenue collection and Tax-to-GDP ratio.
    """
    def validate_configuration(self) -> None:
        pass

    async def fetch(self) -> Any:
        self.fetch_time = datetime.now(timezone.utc)
        self.source_url = self.config.get("url", "https://www.fbr.gov.pk/")
        fetched = {}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(headers=headers, timeout=25.0, follow_redirects=True, verify=False) as client:

            # 1. World Bank API — primary source for Tax-to-GDP (Pakistan GC.TAX.TOTL.GD.ZS)
            wb_urls = [
                "https://api.worldbank.org/v2/country/PAK/indicator/GC.TAX.TOTL.GD.ZS?format=json&per_page=5",
                "https://api.worldbank.org/v2/country/pk/indicator/GC.TAX.TOTL.GD.ZS?format=json&per_page=5&mrv=3",
            ]
            for wb_url in wb_urls:
                if "tax_to_gdp" in fetched:
                    break
                try:
                    res = await client.get(wb_url)
                    if res.status_code == 200:
                        data = res.json()
                        if len(data) > 1 and isinstance(data[1], list):
                            for item in data[1]:
                                if item.get("value") is not None:
                                    fetched["tax_to_gdp"] = round(float(item["value"]), 2)
                                    logger.info(f"FBR Tax-to-GDP from World Bank: {fetched['tax_to_gdp']}%")
                                    break
                except Exception as e:
                    logger.warning(f"FBR World Bank API error ({wb_url}): {e}")

            # 2. FBR Portal scrape — best-effort for tax revenue collection figure
            fbr_urls = [
                "https://www.fbr.gov.pk/",
                "https://www.fbr.gov.pk/statistics",
            ]
            for fbr_url in fbr_urls:
                if "tax_revenue_trillion" in fetched:
                    break
                try:
                    res_fbr = await client.get(fbr_url, timeout=15.0)
                    if res_fbr.status_code == 200:
                        soup = BeautifulSoup(res_fbr.text, 'html.parser')
                        text = soup.get_text()
                        matches = re.findall(
                            r'(?:tax|revenue|collection).*?(?:Rs\.?|PKR)?\s*([\d\.]+\s*(?:Trillion|Billion))',
                            text, re.IGNORECASE
                        )
                        for m in matches:
                            val_str = m.strip()
                            num_m = re.search(r'([\d\.]+)', val_str)
                            if num_m:
                                val = float(num_m.group(1))
                                if 2020 <= val <= 2030:
                                    continue
                                if "billion" in val_str.lower():
                                    val = val / 1000.0
                                if 0.1 <= val <= 20.0:
                                    fetched["tax_revenue_trillion"] = round(val, 2)
                                    logger.info(f"FBR Tax Revenue from portal: {fetched['tax_revenue_trillion']} Trillion PKR")
                                    break
                except Exception as e:
                    logger.warning(f"FBR portal scrape error ({fbr_url}): {e}")

        if not fetched:
            logger.warning("FBR connector: all data sources unavailable. Returning empty result.")

        self.raw_payload = fetched
        return fetched

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        now_iso = self.fetch_time.isoformat()
        normalized = []

        if isinstance(raw_data, dict):
            if "tax_to_gdp" in raw_data and raw_data["tax_to_gdp"] is not None:
                normalized.append({
                    "indicator_code": "FBR_TAX_GDP",
                    "indicator_name": "FBR Tax-to-GDP Ratio",
                    "unit": "% of GDP",
                    "source": "World Bank / FBR Pakistan",
                    "value": float(raw_data["tax_to_gdp"]),
                    "timestamp": now_iso
                })
            if "tax_revenue_trillion" in raw_data and raw_data["tax_revenue_trillion"] is not None:
                normalized.append({
                    "indicator_code": "FBR_TAX_REVENUE",
                    "indicator_name": "FBR Tax Revenue Collection",
                    "unit": "Trillion PKR",
                    "source": "Federal Board of Revenue (FBR)",
                    "value": float(raw_data["tax_revenue_trillion"]),
                    "timestamp": now_iso
                })

        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        """
        Returns True even if no records were fetched — external source unavailability
        is not a connector bug. The manager will handle the 0-record case gracefully.
        """
        if len(normalized_data) == 0:
            logger.warning("FBR validate: no live records fetched (external sources may be unavailable). Skipping persist.")
        return True

    async def persist(self, valid_data: List[Dict[str, Any]]) -> None:
        if not self.db or not valid_data:
            return

        for item in valid_data:
            code = item["indicator_code"]
            name = item["indicator_name"]
            unit = item.get("unit", "")
            val = float(item["value"])
            ts = datetime.fromisoformat(item["timestamp"])

            stmt = select(EconomicIndicator).where(EconomicIndicator.code == code)
            res = await self.db.execute(stmt)
            ind = res.scalars().first()

            if not ind:
                ind = EconomicIndicator(
                    id=uuid.uuid4(),
                    code=code,
                    name=name,
                    description=name,
                    is_active=True,
                )
                self.db.add(ind)
                await self.db.flush()

                meta = IndicatorMetadata(
                    id=uuid.uuid4(),
                    indicator_id=ind.id,
                    unit=unit,
                    frequency="monthly",
                    source_agency="Federal Board of Revenue (FBR)",
                )
                self.db.add(meta)
                await self.db.flush()

            obs = IndicatorObservation(
                id=uuid.uuid4(),
                indicator_id=ind.id,
                timestamp=ts,
                value=val
            )
            self.db.add(obs)

        await self.db.commit()
        logger.info(f"FBR persist: Written {len(valid_data)} records to database.")

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": "FBR Live Data Engine",
            "url": getattr(self, "source_url", "https://www.fbr.gov.pk/"),
            "retrieved_at": getattr(self, "fetch_time", None)
        }
