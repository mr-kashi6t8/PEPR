import uuid
import logging
from typing import Any, Dict, List
from datetime import datetime, timezone
import re
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from app.services.ingestion.connector_base import DataSourceConnector
from app.models.news import NewsArticle
from app.models.ingestion import DataSource
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger("pepr.youtube")


class YouTubeConnector(DataSourceConnector):
    """
    Ingests text transcripts from YouTube videos (e.g. news channels, economic talk shows).
    Provides raw text to the M3 NLP engine for topic modeling and sentiment analysis.
    """

    def validate_configuration(self) -> None:
        if "video_ids" not in self.config and "channel_ids" not in self.config:
            raise ValueError("YouTubeConnector requires 'video_ids' or 'channel_ids' in configuration.")

    def _extract_video_id(self, url_or_id: str) -> str:
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url_or_id)
        return match.group(1) if match else url_or_id

    async def fetch(self) -> Any:
        video_items = []
        channel_ids = self.config.get("channel_ids", [])
        video_ids = list(self.config.get("video_ids", []))

        # 1. Fetch video metadata from YouTube channel RSS feeds
        for channel_id in channel_ids:
            try:
                feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:25]:
                    v_id = entry.get('yt_videoid') or entry.get('id', '').split(':')[-1]
                    if v_id:
                        video_items.append({
                            "video_id": v_id,
                            "title": entry.get('title', f"YouTube Video {v_id}"),
                            "link": entry.get('link', f"https://youtube.com/watch?v={v_id}"),
                            "published": entry.get('published', datetime.now(timezone.utc).isoformat()),
                            "summary": entry.get('summary', entry.get('title', ''))
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch channel RSS for {channel_id}: {e}")

        # Add explicit video_ids if present
        existing_ids = {item["video_id"] for item in video_items}
        for v_id in video_ids:
            clean_id = self._extract_video_id(v_id)
            if clean_id not in existing_ids:
                video_items.append({
                    "video_id": clean_id,
                    "title": f"YouTube Video {clean_id}",
                    "link": f"https://youtube.com/watch?v={clean_id}",
                    "published": datetime.now(timezone.utc).isoformat(),
                    "summary": ""
                })

        if not video_items and channel_ids:
            for channel_id in channel_ids:
                video_items.append({
                    "video_id": f"channel-{channel_id}",
                    "title": f"YouTube Channel {channel_id}",
                    "link": f"https://www.youtube.com/channel/{channel_id}",
                    "published": datetime.now(timezone.utc).isoformat(),
                    "summary": "Channel metadata fallback because the feed returned no videos."
                })

        raw_transcripts = []

        for item in video_items:
            v_id = item["video_id"]
            transcript_text = ""
            
            # 2. Try fetching transcripts via YouTubeTranscriptApi
            try:
                t_list = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'ur', 'hi', 'en-US'])
                transcript_text = " ".join([t.get('text', '') for t in t_list if t.get('text')])
            except Exception:
                try:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(v_id)
                    t_obj = next(iter(transcript_list))
                    fetched_data = t_obj.fetch()
                    transcript_text = " ".join([t.get('text', '') for t in fetched_data if t.get('text')])
                except Exception as tr_err:
                    logger.debug(f"Transcript API unavailable for {v_id}: {tr_err}. Using RSS video metadata.")
                    transcript_text = f"{item['title']}. {item['summary']}"

            if not transcript_text:
                transcript_text = f"{item['title']}. {item['summary']}"

            raw_transcripts.append({
                "video_id": v_id,
                "title": item["title"],
                "url": item["link"],
                "text": transcript_text,
                "fetched_at": item["published"]
            })

        if not raw_transcripts and channel_ids:
            for channel_id in channel_ids:
                raw_transcripts.append({
                    "video_id": f"channel-{channel_id}",
                    "title": f"YouTube Channel {channel_id}",
                    "url": f"https://www.youtube.com/channel/{channel_id}",
                    "text": f"YouTube channel metadata for {channel_id}",
                    "fetched_at": datetime.now(timezone.utc),
                })

        return raw_transcripts

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        normalized = []
        for item in raw_data:
            normalized.append({
                "title": f"YouTube Talkshow: {item['title']}",
                "url": item["url"],
                "published_at": item["fetched_at"],
                "content": item["text"],
            })
        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        return len(normalized_data) > 0

    async def _get_or_create_data_source(self) -> uuid.UUID:
        source_name = self.config.get("source_name", "YouTube Economy Shows")
        result = await self.db.execute(
            select(DataSource).where(DataSource.name == source_name)
        )
        ds = result.scalars().first()
        if ds:
            return ds.id
        ds = DataSource(
            id=uuid.uuid4(),
            name=source_name,
            source_type="youtube",
            base_url="https://youtube.com",
            is_active=True,
        )
        self.db.add(ds)
        await self.db.flush()
        return ds.id

    async def persist(self, valid_data: List[Dict[str, Any]]) -> None:
        if not self.db or not valid_data:
            return

        source_id = await self._get_or_create_data_source()
        inserted = 0
        for item in valid_data:
            try:
                pub_at = item.get("published_at")
                if isinstance(pub_at, str):
                    try:
                        pub_at = datetime.fromisoformat(pub_at)
                    except Exception:
                        pub_at = datetime.now(timezone.utc)

                stmt = pg_insert(NewsArticle).values(
                    id=uuid.uuid4(),
                    source_id=source_id,
                    title=item["title"][:500],
                    url=item["url"][:1000],
                    content=item.get("content", ""),
                    published_at=pub_at or datetime.now(timezone.utc),
                ).on_conflict_do_nothing(index_elements=["url"])
                await self.db.execute(stmt)
                inserted += 1
            except Exception as e:
                logger.warning(f"Skipping youtube item {item.get('url', '?')}: {e}")

        await self.db.commit()
        logger.info(f"YouTube persist: {inserted} video items/transcripts written to news_articles table")

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": "YouTubeConnector",
            "channel_ids": self.config.get("channel_ids", []),
        }
