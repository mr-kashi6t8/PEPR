# Development Roadmap

The development of PEPR is broken into independently testable milestones.

## Milestone 1: Architecture & Foundation (Current)
- [x] Create repository structure.
- [x] Draft architecture and design documents.
- [ ] Implement `setup.ps1` and verify local database connections (Postgres, Redis, Qdrant).

## Milestone 2: Backend Core & AI Gateway
- [ ] Setup FastAPI skeleton with SQLAlchemy and Alembic.
- [ ] Implement JWT Authentication and Role-Based Access.
- [ ] Build the AI Gateway with OpenRouter integration, cost tracking, and token logging.
- **Verification**: Pytest suite for Auth and mock AI Gateway calls.

## Milestone 3: Data Ingestion Engine
- [ ] Setup Celery and Redis integration.
- [ ] Implement abstract Connector logic.
- [ ] Build SBP API Connector.
- [ ] Build Dawn/Tribune RSS Connectors.
- **Verification**: Run Celery worker and verify data lands in PostgreSQL `data_points`.

## Milestone 4: RAG Engine
- [ ] Setup Qdrant collections.
- [ ] Implement PDF/Text chunking and local embedding generation.
- [ ] Build the Semantic Search API.
- **Verification**: Ingest a sample PIDE document and successfully retrieve context.

## Milestone 5: ML & Trend Engine
- [ ] Implement scikit-learn Isolation Forest on numerical time-series.
- [ ] Save anomalies to the database.
- **Verification**: Inject dummy anomalous data into Postgres and verify the ML engine flags it.

## Milestone 6: Report Engine
- [ ] Build the Celery scheduled task for weekly reporting.
- [ ] Aggregation logic (combining anomalies, news, and RAG context).
- [ ] Prompt engineering for the final report generation via AI Gateway.
- **Verification**: Manually trigger report generation and inspect Markdown/JSON output.

## Milestone 7: Frontend Dashboard
- [ ] Setup Vite + React + Tailwind + shadcn.
- [ ] Build Login/Auth flow.
- [ ] Build main Dashboard (ECharts for time-series).
- [ ] Build Report Viewer interface.
- **Verification**: Full E2E manual walkthrough of the UI.
