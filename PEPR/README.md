# Pakistan Economic Problem Radar (PEPR)

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)

**PEPR (Pakistan Economic Problem Radar)** is a production-grade, AI-powered economic intelligence platform. It systematically ingests, analyzes, and synthesizes macroeconomic indicators, policy updates, news, and research from key Pakistani sources (PBS, SBP, PSX, FBR, World Bank, news RSS feeds) to detect economic anomalies, forecast trends, and generate automated weekly insights.

---

## 🌟 Key Features & Core Engines

- 🔌 **Data Ingestion Engine (M1)**: Automated background collectors for macroeconomic & financial data sources (PBS, SBP, PSX, FBR, World Bank, RSS feeds, YouTube transcripts).
- 📈 **Trend & ML Engine (M2)**: Time-series statistical analysis combined with `scikit-learn` Isolation Forest models for automated anomaly detection across economic indicators.
- 📚 **RAG Engine (M5)**: Hybrid Retrieval-Augmented Generation using local `sentence-transformers` embeddings and Qdrant vector database to index and retrieve research documents (PIDE papers, economic reports).
- 📝 **Report Generation Engine (M6)**: Automated weekly report generation synthesizing ingested news, statistical anomalies, and RAG context via an integrated LLM gateway.
- 🤖 **AI Gateway**: Centralized, secure internal LLM router (supporting OpenRouter, Gemini, GPT-4o-mini) with token control, automated retries, and structured JSON output validation.
- 📊 **Interactive Dashboard**: Modern React 19 + Vite dashboard featuring real-time economic charts, indicator tracking, problem synthesis, research search, and report viewing.

---

## 🏗️ Project Architecture & Repository Structure

PEPR is organized as a clean **Monorepo** adhering to best-practice separation of concerns:

```
PEPR/
├── docs/                        # Architecture & system design documentation
│   ├── ARCHITECTURE.md          # High-level technical architecture
│   ├── SYSTEM_DESIGN.md        # Core engine & module specifications
│   ├── API_DESIGN.md           # API REST endpoint guidelines
│   ├── DATABASE_DESIGN.md      # PostgreSQL schema & entity designs
│   ├── DATA_SOURCE_STRATEGY.md  # Connectors & scraping specifications
│   ├── DEPLOYMENT_DESIGN.md    # Deployment & environment configurations
│   ├── DEVELOPMENT_ROADMAP.md # Feature roadmap & milestone goals
│   ├── PROJECT_RULES.md        # Code standards & contributor guidelines
│   └── SECURITY_DESIGN.md      # Auth & API security architecture
│
├── backend/                     # Python / FastAPI Backend Server
│   ├── alembic/                 # Database migrations (Alembic)
│   ├── app/                     # FastAPI core application logic
│   │   ├── api/v1/endpoints/    # REST API endpoints (indicators, news, alerts, etc.)
│   │   ├── core/                # Configuration, auth, logging, AI gateway, Celery
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── repositories/        # Database access layer
│   │   ├── services/            # Core business logic (ingestion, nlp, analysis, rag)
│   │   └── templates/           # HTML/Jinja2 report export templates
│   ├── scripts/                 # Utility & helper scripts (organized by function)
│   │   ├── checks/              # Diagnostic & DB verification scripts
│   │   ├── maintenance/         # Cleanup & job maintenance utilities
│   │   ├── runners/             # Live pipeline execution & trigger scripts
│   │   └── dev/                 # Developer setup & configuration tools
│   ├── tests/                   # Backend pytest test suite
│   ├── .env.example             # Backend environment template
│   ├── alembic.ini              # Alembic config
│   ├── requirements.txt         # Python dependencies
│   └── sources.json             # Ingestion catalog configuration
│
└── frontend/                    # React 19 + TypeScript + Vite Frontend App
    ├── public/                  # Static web assets
    ├── src/
    │   ├── api/                 # API client, TypeScript types, and custom hooks
    │   ├── components/          # Reusable UI, layout, auth, & chart components
    │   ├── context/             # Global React state contexts (AuthContext)
    │   └── pages/               # Top-level view pages (Dashboard, Trends, Reports)
    ├── package.json             # NPM dependencies & scripts
    ├── vite.config.ts           # Vite bundler setup
    └── vercel.json              # Vercel deployment configuration
```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Python 3.11+, FastAPI, Uvicorn
- **Database**: PostgreSQL with SQLAlchemy 2.0 (AsyncPG) & Alembic
- **Async Workers**: Celery + Redis
- **Vector DB**: Qdrant Vector Database
- **Machine Learning**: Scikit-Learn (Isolation Forest), Pandas, NumPy
- **RAG & NLP**: PyMuPDF, Sentence-Transformers, TextBlob, LangDetect
- **LLM Gateway**: Instructor / OpenAI / OpenRouter client

### Frontend
- **Framework**: React 19, TypeScript, Vite
- **Styling**: Tailwind CSS, Lucide Icons
- **State & Data Fetching**: TanStack Query (React Query)
- **Charts**: Recharts

---

## 🚀 Getting Started for Collaborators

Follow these instructions to set up the PEPR development environment locally.

### 1. Prerequisites
Ensure you have the following installed on your system:
- **Python** `^3.11`
- **Node.js** `^18.0.0` & **npm**
- **PostgreSQL** Database server (running on port `5432`)
- **Redis** Server (running on port `6379`)
- **Qdrant** Vector DB (running on port `6333` or local file mode)

---

### 2. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd PEPR/backend
   ```

2. **Create and activate a Python virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your database credentials and API keys:
   ```bash
   cp .env.example .env
   ```
   Update `.env` with:
   - `DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/pepr_db`
   - `REDIS_URL=redis://localhost:6379/0`
   - `OPENROUTER_API_KEY=your_key_here`

5. **Run Database Migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the Development Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The backend API documentation will be available at:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

7. **Run Celery Workers (Optional, for background ingestion/jobs)**:
   ```bash
   celery -A app.core.celery.celery_app worker --loglevel=info
   ```

---

### 3. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd PEPR/frontend
   ```

2. **Install node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   The dashboard will be accessible at `http://localhost:5173`.

---

## 🧪 Testing & Utilities

### Running Backend Tests
Execute pytest from the `backend/` folder:
```bash
cd PEPR/backend
pytest tests/
```

### Running Utility Scripts
Utility scripts are categorized in `backend/scripts/`:
- **Run Live Data Ingestion**:
  ```bash
  python -m scripts.runners.run_live_ingestion
  ```
- **Check Indicator Database**:
  ```bash
  python -m scripts.checks.check_indicators_db
  ```
- **Run Anomaly & Trend Engine**:
  ```bash
  python -m scripts.runners.run_trend_and_anomaly_engine
  ```

---

## 📚 Further Documentation

For deep technical details, please refer to the documents inside the [`docs/`](./docs) folder:
- [Architecture Overview](./docs/ARCHITECTURE.md)
- [System & Module Design](./docs/SYSTEM_DESIGN.md)
- [API Design Guidelines](./docs/API_DESIGN.md)
- [Database Entity Schemas](./docs/DATABASE_DESIGN.md)
- [Data Source & Scraper Strategy](./docs/DATA_SOURCE_STRATEGY.md)
- [Security & Authentication](./docs/SECURITY_DESIGN.md)

---

## 📄 License

This project is developed as part of the **PIDE (Pakistan Institute of Development Economics)** Internship Program. All rights reserved.
