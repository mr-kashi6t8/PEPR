import inspect
import feedparser
import httpx
import uuid
import logging
from typing import Any, Dict, List
from datetime import datetime, timezone
import time

from app.services.ingestion.connector_base import DataSourceConnector
from app.models.news import NewsArticle
from app.models.ingestion import DataSource
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger("pepr.rss")


class RSSConnector(DataSourceConnector):

    async def _await_if_needed(self, value: Any) -> Any:
        if inspect.isawaitable(value):
            return await value
        return value

    def validate_configuration(self) -> None:
        if "rss_url" not in self.config and not self.config.get("rss_urls"):
            raise ValueError("RSSConnector requires 'rss_url' or non-empty 'rss_urls' in config")

    def _candidate_urls(self) -> List[str]:
        urls: List[str] = []
        primary = self.config.get("rss_url")
        if primary:
            urls.append(primary)

        for url in self.config.get("rss_urls", []):
            if url and url not in urls:
                urls.append(url)

        return urls

    async def fetch(self) -> Any:
        self.fetch_time = datetime.now(timezone.utc)
        candidate_urls = self._candidate_urls()
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for url in candidate_urls:
                self.source_url = url
                try:
                    response = await self._request(client, "GET", self.source_url)
                    self.raw_payload = response.text
                    return self.raw_payload
                except Exception as exc:
                    last_error = exc
                    logger.warning("RSS fetch failed for %s: %s", url, exc)
                    continue

        if last_error:
            raise last_error
        raise ValueError("No RSS URL candidates configured")

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        parsed = feedparser.parse(raw_data)
        normalized = []
        for entry in parsed.entries:
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime.fromtimestamp(
                    time.mktime(entry.published_parsed), tz=timezone.utc
                )
            else:
                published = datetime.now(timezone.utc)

            title = getattr(entry, 'title', '')
            url = getattr(entry, 'link', '')
            summary = getattr(entry, 'summary', '')

            # Attempt NLP processing - gracefully degrade if unavailable
            try:
                from app.services.nlp.text_processor import TextProcessor
                nlp_data = TextProcessor.process_article(
                    url=url, html_content=summary, title=title
                )
                sentiment = float(nlp_data.get("sentiment_score", 0.0))
                language = nlp_data.get("language", "en")
                clean_content = nlp_data.get("clean_text", summary)
                canonical_url = nlp_data.get("canonical_url", url)
            except Exception as nlp_err:
                logger.warning(f"NLP failed for {url}: {nlp_err}")
                sentiment = 0.0
                language = "en"
                clean_content = summary
                canonical_url = url

            if not title and not canonical_url and not clean_content:
                continue

            normalized.append({
                "title": title,
                "url": canonical_url,
                "content": clean_content,
                "language": language,
                "sentiment_score": sentiment,
                "published_at": published,
                "source_name": self.config.get("source_name", "RSS Feed"),
                "rss_url": self.source_url,
            })
        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        if not normalized_data:
            raise ValueError("Validation failed: No valid RSS entries were produced after normalization")

        for item in normalized_data:
            if not item.get("title") or not item.get("url"):
                raise ValueError(f"Validation failed: Malformed RSS entry: {item}")
        return True

    async def _get_or_create_data_source(self, source_name: str, rss_url: str) -> uuid.UUID:
        """Resolve or create a DataSource row so we have a valid FK for news_articles."""
        if not self.db:
            return uuid.uuid4()

        result = await self._await_if_needed(self.db.execute(select(DataSource).where(DataSource.name == source_name)))
        ds = result.scalars().first()
        if ds:
            return ds.id

        ds = DataSource(
            id=uuid.uuid4(),
            name=source_name,
            source_type="rss",
            base_url=rss_url,
            is_active=True,
        )
        self.db.add(ds)
        await self._await_if_needed(self.db.flush())  # get id without full commit
        return ds.id

    async def persist(self, valid_data: List[Dict[str, Any]]) -> None:
        """
        Upserts news articles into news_articles table.
        ON CONFLICT DO NOTHING on url for full idempotency.
        """
        if not self.db or not valid_data:
            return

        if not self.db:
            logger.info("RSS persist skipped: no database session attached")
            return

        rss_url = getattr(self, "source_url", self.config.get("rss_url", ""))
        source_name = self.config.get("source_name", "RSS Feed")
        source_id = await self._get_or_create_data_source(source_name, rss_url)

        inserted = 0
        for item in valid_data:
            try:
                stmt = pg_insert(NewsArticle).values(
                    id=uuid.uuid4(),
                    source_id=source_id,
                    title=item["title"][:500],
                    url=item["url"][:1000],
                    content=item.get("content", ""),
                    published_at=item.get("published_at", datetime.now(timezone.utc)),
                ).on_conflict_do_nothing(index_elements=["url"])
                await self._await_if_needed(self.db.execute(stmt))
                inserted += 1
            except Exception as e:
                logger.warning(f"Skipping article {item.get('url', '?')}: {e}")

        await self._await_if_needed(self.db.commit())
        logger.info(f"RSS persist: {inserted}/{len(valid_data)} articles written to DB for {source_name}")

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source_url": getattr(self, "source_url", ""),
            "retrieval_timestamp": getattr(self, "fetch_time", None),
        }
