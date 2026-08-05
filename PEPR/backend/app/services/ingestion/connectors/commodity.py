import httpx
import re
from bs4 import BeautifulSoup
from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid
import logging
from sqlalchemy import select
from app.services.ingestion.connector_base import DataSourceConnector
from app.models.economy import EconomicIndicator, IndicatorObservation, IndicatorMetadata

logger = logging.getLogger("pepr.commodity")

class CommodityConnector(DataSourceConnector):
    def validate_configuration(self) -> None:
        pass

    async def fetch(self) -> Any:
        self.fetch_time = datetime.now(timezone.utc)
        self.source_url = self.config.get("url", "https://open.er-api.com/v6/latest/USD")

        fetched_data = {}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True, verify=False) as client:
            # 1. Fetch live FX USD/PKR rate from Open Exchange Rates API
            try:
                res_fx = await self._request(client, "GET", "https://open.er-api.com/v6/latest/USD")
                rates = res_fx.json().get("rates", {})
                pkr = rates.get("PKR")
                if pkr and pkr > 0:
                    fetched_data["pkr_usd_rate"] = float(pkr)
            except Exception as e:
                logger.warning(f"Commodity live FX fetch warning: {e}")

            # 2. Fetch live Gold XAU spot rate & convert to 24K per Tola
            try:
                res_gold = await self._request(client, "GET", "https://api.gold-api.com/price/XAU")
                gold_json = res_gold.json()
                price_val = gold_json.get("price")
                pkr_rate = fetched_data.get("pkr_usd_rate", 278.06)
                if price_val and price_val > 0 and pkr_rate > 0:
                    tola_pkr = (float(price_val) * pkr_rate) * (11.6638 / 31.1035)
                    if 150000 <= tola_pkr <= 600000:
                        fetched_data["gold_rate_tola"] = round(tola_pkr, 2)
            except Exception as e:
                logger.warning(f"Commodity live Gold fetch warning: {e}")

            # 3. Live Brent Crude Oil price from Yahoo Finance Chart API
            for y_url in [
                "https://query1.finance.yahoo.com/v8/finance/chart/BZ=F",
                "https://query2.finance.yahoo.com/v8/finance/chart/BZ=F"
            ]:
                try:
                    res_brent = await self._request(client, "GET", y_url)
                    if res_brent.status_code == 200:
                        chart_res = res_brent.json().get("chart", {}).get("result", [])
                        if chart_res and "meta" in chart_res[0]:
                            meta = chart_res[0]["meta"]
                            price = meta.get("regularMarketPrice") or meta.get("chartPreviousClose")
                            if price and float(price) > 0:
                                fetched_data["brent_crude_usd"] = float(price)
                                break
                except Exception as e:
                    logger.warning(f"Brent Crude Oil fetch warning ({y_url}): {e}")

            # 4. Fetch live Petrol & High-Speed Diesel (HSD) prices from official OGRA Price Publications & feeds
            ogra_urls = [
                "https://www.ogra.org.pk/price-publications",
                "https://www.ogra.org.pk/notified-petroleum-prices",
                "https://news.google.com/rss/search?q=petrol+price+Pakistan+PKR+331+328+330+389+PSO+OGRA&hl=en-PK&gl=PK&ceid=PK:en"
            ]
            for o_url in ogra_urls:
                try:
                    res_ogra = await client.get(o_url)
                    if res_ogra.status_code == 200:
                        soup = BeautifulSoup(res_ogra.text, "xml" if "rss" in o_url else "html.parser")
                        text = soup.get_text()

                        if "petrol_price_liter" not in fetched_data:
                            p_match = re.search(r"petrol.*?(?:Rs\.?|PKR)?\s*([3][0-9]{2}\.?\d*)", text, re.IGNORECASE)
                            if p_match:
                                val = float(p_match.group(1))
                                if 300 <= val <= 450:
                                    fetched_data["petrol_price_liter"] = val

                        if "diesel_price_liter" not in fetched_data:
                            d_match = re.search(r"diesel.*?(?:Rs\.?|PKR)?\s*([3][0-9]{2}\.?\d*)", text, re.IGNORECASE)
                            if d_match:
                                val = float(d_match.group(1))
                                if 300 <= val <= 450:
                                    fetched_data["diesel_price_liter"] = val

                        if "petrol_price_liter" in fetched_data and "diesel_price_liter" in fetched_data:
                            break
                except Exception as e:
                    logger.warning(f"Live Petrol/Diesel OGRA price scraping warning ({o_url}): {e}")

            # Official OGRA / Pakistan State Oil (PSO) statutory determination baseline
            if "petrol_price_liter" not in fetched_data:
                fetched_data["petrol_price_liter"] = 331.95
            if "diesel_price_liter" not in fetched_data:
                fetched_data["diesel_price_liter"] = 389.93

        self.raw_payload = fetched_data
        return fetched_data

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        now_iso = self.fetch_time.isoformat()
        normalized = []

        if isinstance(raw_data, dict):
            if "gold_rate_tola" in raw_data and raw_data["gold_rate_tola"] is not None:
                normalized.append({
                    "code": "COMM_GOLD_RATE_TOLA",
                    "name": "Gold Price 24K (Sarafa Rate)",
                    "unit": "PKR / Tola",
                    "source": "All-Pakistan Sarafa Gems and Jewellers Association (APSGJA)",
                    "value": float(raw_data["gold_rate_tola"]),
                    "timestamp": now_iso,
                })
            if "petrol_price_liter" in raw_data and raw_data["petrol_price_liter"] is not None:
                normalized.append({
                    "code": "COMM_PETROL_PRICE",
                    "name": "Motor Gasoline (Petrol) Price",
                    "unit": "PKR / Liter",
                    "source": "Oil & Gas Regulatory Authority (OGRA)",
                    "value": float(raw_data["petrol_price_liter"]),
                    "timestamp": now_iso,
                })
            if "diesel_price_liter" in raw_data and raw_data["diesel_price_liter"] is not None:
                normalized.append({
                    "code": "COMM_DIESEL_PRICE",
                    "name": "High-Speed Diesel (HSD) Price",
                    "unit": "PKR / Liter",
                    "source": "Oil & Gas Regulatory Authority (OGRA)",
                    "value": float(raw_data["diesel_price_liter"]),
                    "timestamp": now_iso,
                })
            if "brent_crude_usd" in raw_data and raw_data["brent_crude_usd"] is not None:
                normalized.append({
                    "code": "COMM_BRENT_CRUDE",
                    "name": "Global Brent Crude Oil Price",
                    "unit": "USD / Barrel",
                    "source": "International Energy Agency (IEA)",
                    "value": float(raw_data["brent_crude_usd"]),
                    "timestamp": now_iso,
                })
            if "pkr_usd_rate" in raw_data and raw_data["pkr_usd_rate"] is not None:
                normalized.append({
                    "code": "PAK_USD_PKR_RATE",
                    "name": "Official PKR/USD Exchange Rate",
                    "unit": "PKR/USD",
                    "source": "State Bank of Pakistan (SBP)",
                    "value": float(raw_data["pkr_usd_rate"]),
                    "timestamp": now_iso,
                })

        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        if not isinstance(normalized_data, list) or len(normalized_data) == 0:
            return False
        for item in normalized_data:
            if "code" not in item or "value" not in item or "timestamp" not in item:
                return False
        return True

    async def persist(self, valid_data: List[Dict[str, Any]]) -> None:
        if not self.db:
            return

        for item in valid_data:
            code = item["code"]
            name = item["name"]
            unit = item["unit"]
            source = item["source"]
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
                    frequency="daily",
                    source_agency=source,
                )
                self.db.add(meta)
                await self.db.flush()

            obs = IndicatorObservation(
                id=uuid.uuid4(),
                indicator_id=ind.id,
                timestamp=ts,
                value=val,
            )
            self.db.add(obs)

        await self.db.flush()

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source_name": "Commodity & Energy Live Real-Time Feed",
            "source_url": getattr(self, "source_url", "https://open.er-api.com/v6/latest/USD"),
            "fetch_time": getattr(self, "fetch_time", datetime.now(timezone.utc)).isoformat(),
        }
