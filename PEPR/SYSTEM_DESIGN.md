# System Design

## 1. AI Gateway
A dedicated internal module (`backend/app/core/ai_gateway.py`).
- **Responsibilities**: Route prompts to OpenRouter, enforce token limits, handle retries, and validate structured JSON output.
- **Config**: Driven by environment variables (`LLM_MODEL`, `FALLBACK_MODEL`).

## 2. Data Ingestion Engine (M1)
Runs as scheduled Celery tasks.
- **Connectors Module**: Abstract base classes for Data Sources.
- **Implementations**: `PBSConnector`, `SBPConnector`, `PSXConnector`, `RSSConnector`.

## 3. Trend & ML Engine (M2)
- **Anomaly Detection**: Uses scikit-learn `IsolationForest`.
- **Time-Series Analysis**: Custom robust statistical analysis. Prophet is restricted to statistically justified use cases only.

## 4. RAG Engine (M5)
- **Indexer**: Reads PDF/Text, chunks via LangChain/LlamaIndex utilities, embeds via local `sentence-transformers`.
- **Storage**: Upserts vectors + metadata into Qdrant.
- **Retriever**: Performs similarity search, strictly preserving citations for the LLM context window.

## 5. Report Engine (M6)
- **Trigger**: Weekly CRON job in Celery.
- **Process**: Aggregates anomalies from M2, summarizes news from M1, queries RAG from M5, passes all to AI Gateway.
- **Output**: Generates a final JSON/Markdown report stored in PostgreSQL for the frontend.
