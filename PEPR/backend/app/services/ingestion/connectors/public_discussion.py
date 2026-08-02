import logging
import uuid
import time
from urllib.parse import quote_plus
from datetime import datetime, timezone
from typing import Any, Dict, List

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.ingestion import DataSource
from app.models.news import NewsArticle
from app.services.ingestion.connector_base import DataSourceConnector

logger = logging.getLogger("pepr.public_discussion")


class PublicDiscussionConnector(DataSourceConnector):
    """
    Config-driven connector for free public discussion sources.
    Supports multiple RSS feeds and keeps source definitions declarative.
    """

    def validate_configuration(self) -> None:
        feeds = self.config.get("feeds", [])
        if not isinstance(feeds, list) or not feeds:
            raise ValueError("PublicDiscussionConnector requires a non-empty 'feeds' list in config")

    async def fetch(self) -> Any:
        self.fetch_time = datetime.now(timezone.utc)
        feeds = self.config.get("feeds", [])
        collected: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for feed_cfg in feeds:
                source_ref = feed_cfg.get("rss_url") or feed_cfg.get("query") or feed_cfg.get("name") or "public_discussion"
                try:
                    source_type = (feed_cfg.get("type") or "rss").lower()
                    source_name = feed_cfg.get("source_name") or feed_cfg.get("name") or feed_cfg.get("rss_url") or feed_cfg.get("query") or "Public Discussion"

                    if source_type == "gdelt":
                        query = feed_cfg.get("query")
                        if not query:
                            continue

                        gdelt_url = (
                            "https://api.gdeltproject.org/api/v2/doc/doc"
                            f"?query={quote_plus(query)}&mode=ArtList&format=json&sort=hybridrel&maxrecords={int(feed_cfg.get('limit', 20))}"
                        )
                        response = await self._request(client, "GET", gdelt_url)
                        payload = response.json()
                        for article in payload.get("articles", [])[: feed_cfg.get("limit", 20)]:
                            title = (article.get("title") or "").strip()
                            url = (article.get("url") or "").strip()
                            if not title or not url:
                                continue

                            published_at = datetime.now(timezone.utc)
                            seendate = article.get("seendate") or article.get("datetime")
                            if isinstance(seendate, str) and len(seendate) >= 8:
                                try:
                                    published_at = datetime.fromisoformat(seendate.replace("Z", "+00:00"))
                                except ValueError:
                                    pass

                            collected.append(
                                {
                                    "source_name": source_name,
                                    "feed_url": gdelt_url,
                                    "title": title,
                                    "url": url,
                                    "content": article.get("description") or article.get("sourceCountry") or article.get("domain") or "",
                                    "published_at": published_at,
                                }
                            )
                    else:
                        feed_url = feed_cfg.get("rss_url")
                        if not feed_url:
                            continue

                        response = await self._request(client, "GET", feed_url)
                        feed = feedparser.parse(response.text)

                        for entry in feed.entries[: feed_cfg.get("limit", 20)]:
                            title = getattr(entry, "title", "").strip()
                            url = getattr(entry, "link", "").strip()
                            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                            published = getattr(entry, "published_parsed", None)
                            if published:
                                published_at = datetime.fromtimestamp(
                                    time.mktime(published), tz=timezone.utc
                                )
                            else:
                                published_at = datetime.now(timezone.utc)

                            if not title or not url:
                                continue

                            collected.append(
                                {
                                    "source_name": source_name,
                                    "feed_url": feed_url,
                                    "title": title,
                                    "url": url,
                                    "content": summary,
                                    "published_at": published_at,
                                }
                            )
                except Exception as exc:
                    logger.warning("Failed to fetch public discussion feed %s: %s", source_ref, exc)

        self.raw_payload = collected
        return collected

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for item in raw_data or []:
            normalized.append(
                {
                    "title": item["title"][:500],
                    "url": item["url"][:1000],
                    "content": item.get("content", ""),
                    "published_at": item.get("published_at", datetime.now(timezone.utc)),
                    "source_name": item.get("source_name", "Public Discussion"),
                    "feed_url": item.get("feed_url", ""),
                }
            )
        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        return bool(normalized_data)

    async def _get_or_create_data_source(self, source_name: str, feed_url: str) -> uuid.UUID:
        if not self.db:
            return uuid.uuid4()

        result = await self.db.execute(select(DataSource).where(DataSource.name == source_name))
        source = result.scalars().first()
        if source:
            return source.id

        source = DataSource(
            id=uuid.uuid4(),
            name=source_name,
            source_type="public_discussion",
            base_url=feed_url,
            is_active=True,
        )
        self.db.add(source)
        await self.db.flush()
        return source.id

    async def persist(self, valid_data: List[Dict[str, Any]]) -> None:
        if not self.db or not valid_data:
            return

        inserted = 0
        for item in valid_data:
            source_id = await self._get_or_create_data_source(item.get("source_name", "Public Discussion"), item.get("feed_url", ""))
            stmt = pg_insert(NewsArticle).values(
                id=uuid.uuid4(),
                source_id=source_id,
                title=item["title"],
                url=item["url"],
                content=item.get("content", ""),
                published_at=item.get("published_at", datetime.now(timezone.utc)),
            ).on_conflict_do_nothing(index_elements=["url"])
            await self.db.execute(stmt)
            inserted += 1

        await self.db.commit()
        logger.info("Public discussion persist: %s records written to news_articles", inserted)

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": "Public discussion RSS bundle",
            "feeds": self.config.get("feeds", []),
            "retrieved_at": getattr(self, "fetch_time", None),
        }