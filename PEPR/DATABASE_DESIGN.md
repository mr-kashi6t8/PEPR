# Database Design

## 1. Relational Storage (PostgreSQL)

Managed via SQLAlchemy 2.x and Alembic.

### Key Tables:
- `users`: id, email, password_hash, role, created_at, is_active.
- `sources`: id, name, type (api/rss/html), base_url, status.
- `economic_indicators`: id, source_id, name, unit, frequency.
- `data_points`: id, indicator_id, timestamp, value, raw_json, anomaly_score, is_anomaly.
- `news_articles`: id, source_id, title, url, published_at, content, sentiment_score.
- `reports`: id, generated_at, title, content_markdown, json_data.
- `audit_logs`: id, user_id, action, target, timestamp, ip_address.

## 2. Vector Storage (Qdrant)

Used exclusively for the RAG engine.

### Collections:
- `pide_research`: 
  - Vectors: 768-dim (depending on `sentence-transformers` model).
  - Metadata: title, author, year, pdf_url, chunk_id.
- `news_embeddings`:
  - Vectors: Embeddings of significant economic news.
  - Metadata: article_id, date, source.

## 3. Cache & Queue (Redis)

- Celery Task Queue (`celery` namespace).
- API Response Caching.
- Rate limit tracking counters.
