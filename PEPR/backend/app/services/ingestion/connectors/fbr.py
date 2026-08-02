from bs4 import BeautifulSoup
import httpx
from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid
import re
import logging

from app.services.ingestion.connector_base import DataSourceConnector

logger = logging.getLogger("pepr.fbr")

class FBRConnector(DataSourceConnector):
    """
    Web Scraping Connector for Federal Board of Revenue (FBR) Pakistan.
    Scrapes live tax revenue reports, press releases, and tables directly from fbr.gov.pk.
    """
    def validate_configuration(self) -> None:
        if "url" not in self.config or "fbr.gov.pkr" in self.config.get("url", ""):
            self.config["url"] = "https://www.fbr.gov.pk/"

    async def fetch(self) -> Any:
        url = self.config.get("url", "https://www.fbr.gov.pk/")
        if "fbr.gov.pkr" in url:
            url = "https://www.fbr.gov.pk/"

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.warning(f"FBR live fetch error for {url}: {e}")
            return ""

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        if not raw_data:
            return []

        soup = BeautifulSoup(raw_data, 'html.parser')
        normalized = []

        # 1. Parse tables for revenue collection data
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    category = cols[0].get_text(strip=True)
                    val_text = cols[1].get_text(strip=True)
                    if any(char.isdigit() for char in val_text):
                        normalized.append({
                            "indicator_name": f"FBR Tax Collection - {category[:100]}",
                            "collection_amount": val_text,
                            "raw_text_context": f"{category}: {val_text}",
                            "source_url": self.config.get("url", "https://www.fbr.gov.pk/"),
                            "retrieved_at": datetime.now(timezone.utc).isoformat()
                        })

        # 2. Parse text paragraphs searching for revenue figures
        if not normalized:
            text_blocks = soup.find_all(['p', 'div', 'h3', 'a'])
            for block in text_blocks:
                text = block.get_text(strip=True)
                if "revenue" in text.lower() or "tax" in text.lower() or "collection" in text.lower():
                    amounts = re.findall(r'(?:Rs\.?|PKR)?\s*(\d+[\d,.]*\s*(?:Billion|Trillion|Million|Crore)?)', text, re.IGNORECASE)
                    if amounts and len(text) > 20:
                        normalized.append({
                            "indicator_name": "FBR Federal Revenue Collection",
                            "value_extracted": amounts[0],
                            "raw_text_context": text[:300],
                            "source_url": self.config.get("url", "https://www.fbr.gov.pk/"),
                            "retrieved_at": datetime.now(timezone.utc).isoformat()
                        })
                        if len(normalized) >= 10:
                            break

        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        return len(normalized_data) > 0

    async def persist(self, valid_data: List[Dict[str, Any]]) -> None:
        if not self.db or not valid_data:
            return

        from sqlalchemy import select
        from app.models.economy import EconomicIndicator, IndicatorObservation

        for item in valid_data:
            code = "FBR_TAX_REVENUE"
            val_str = item.get("value_extracted") or item.get("collection_amount")
            if not val_str:
                continue

            digits = re.findall(r'\d+(?:\.\d+)?', str(val_str).replace(',', ''))
            if not digits:
                continue
            val_float = float(digits[0])

            stmt = select(EconomicIndicator).where(EconomicIndicator.code == code)
            result = await self.db.execute(stmt)
            indicator = result.scalar_one_or_none()

            if not indicator:
                indicator = EconomicIndicator(
                    id=uuid.uuid4(),
                    name="FBR Tax Revenue Collection",
                    code=code,
                    description="Federal Board of Revenue Tax Collection",
                    is_active=True
                )
                self.db.add(indicator)
                await self.db.flush()

            obs = IndicatorObservation(
                id=uuid.uuid4(),
                indicator_id=indicator.id,
                timestamp=datetime.now(timezone.utc),
                value=val_float
            )
            self.db.add(obs)

        await self.db.commit()
        logger.info(f"FBR persist: Written {len(valid_data)} records to database.")

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": "FBR Live Web Scraper",
            "url": self.config.get("url", "https://www.fbr.gov.pk/"),
            "scraper_engine": "BeautifulSoup4 + HTTPX"
        }
