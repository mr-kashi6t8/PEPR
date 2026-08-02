# PEPR Architecture Overview

The Pakistan Economic Problem Radar (PEPR) is a production-grade, AI-powered economic intelligence platform. 

## High-Level Architecture
PEPR is designed as a **modular monolith**. It leverages a modern data stack without Docker, running directly on the host using PM2 for process management and PowerShell scripts for environment bootstrapping.

### Core Tiers
1. **Frontend (Presentation Layer)**
   - React + TypeScript + Vite.
   - UI Library: shadcn/ui & Tailwind CSS.
   - Charts: Apache ECharts / Recharts.
   - API Client: TanStack Query.
2. **Backend (Application & API Layer)**
   - Python 3.11+ & FastAPI.
   - Exposes versioned REST APIs (`/api/v1/`).
   - Integrates the **AI Gateway** for centralized, secure LLM communication (OpenRouter).
3. **Asynchronous Task Processing (Data & ML Layer)**
   - Celery + Redis.
   - Responsible for data ingestion, running Isolation Forest anomaly detection, and RAG document chunking.
4. **Data Storage Layer**
   - Relational Data: PostgreSQL (managed by SQLAlchemy 2.x & Alembic).
   - Vector Data: Qdrant (for RAG embeddings via `sentence-transformers`).
   - Key/Value Cache & Message Broker: Redis.

## System Workflow
1. **Ingestion**: Celery workers execute scheduled connectors to pull from APIs and scrape fallback sources.
2. **Analysis**: Time-series and ML workers analyze ingested data for anomalies.
3. **Retrieval**: Documents (PIDE research, news) are embedded and stored in Qdrant.
4. **Synthesis**: The Report Engine utilizes the AI Gateway (passing retrieved contexts via RAG) to generate weekly trend reports.
5. **Consumption**: Users access the insights via the React dashboard.
