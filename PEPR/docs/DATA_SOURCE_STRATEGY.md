# Data Source Strategy

## Primary Philosophy
**API First, Scrape as Fallback**. We prioritize stable, official data channels. Web scraping is inherently brittle and is only used when APIs do not exist.

## Source Integrations (Phase 1)

1. **State Bank of Pakistan (SBP)**
   - **Method**: Official API / Data Portal JSON.
   - **Data**: FX rates, policy rates, monetary metrics.
2. **Pakistan Stock Exchange (PSX)**
   - **Method**: PSX Data Portal APIs.
   - **Data**: KSE-100 historical and daily summaries.
3. **Pakistan Bureau of Statistics (PBS)**
   - **Method**: Web scraping (BeautifulSoup) / PDF Parsing.
   - **Data**: CPI, GDP, Trade stats.
   - **Risk Mitigation**: High failure likelihood. Alerting required on parsing failures.
4. **News (Dawn, Tribune)**
   - **Method**: RSS Feeds (Feedparser).
   - **Data**: English/Urdu news headlines and summaries.

## Data Ingestion Principles
- **Idempotency**: Ingesting the same day's data twice must not create duplicates. We enforce this via unique constraints on `(indicator_id, timestamp)` in Postgres.
- **Provenance**: The `raw_json` and original `url` must be saved before any normalization occurs.
- **Resilience**: If a source fails (HTTP 5xx or structural change), the Celery task must record the failure in the audit log and gracefully exit without discarding previously ingested data.
