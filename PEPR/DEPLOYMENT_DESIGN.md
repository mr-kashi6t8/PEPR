# Deployment Design

## Overview
As per project rules, **Docker is strictly prohibited**. The system is designed to run natively on the host OS (Windows, in this case) using process managers and PowerShell scripts.

## Environment Preparation

### Prerequisites
- Python 3.11+
- Node.js 18+ (for PM2 and React)
- PostgreSQL 15+ (Native Windows Installation)
- Redis (via Memurai or native Windows port)
- Qdrant (Windows binary)

### Bootstrapping
A master `setup.ps1` script will:
1. Create Python virtual environments (`python -m venv venv`).
2. Install Python dependencies (`pip install -r requirements.txt`).
3. Install Node dependencies (`npm install` in frontend).
4. Run Alembic migrations.

## Process Management (PM2)
We will use **PM2** to manage the background processes. An `ecosystem.config.js` will define the services:
- `pepr-api`: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- `pepr-celery-worker`: `celery -A app.core.celery worker --loglevel=info`
- `pepr-celery-beat`: `celery -A app.core.celery beat --loglevel=info`
- `pepr-frontend`: `npm run preview`
- `pepr-qdrant`: execution of Qdrant binary.

## CI/CD Pipeline
- **Testing**: GitHub Actions will run Pytest and ESLint on pull requests.
- **Deployment**: A manual `deploy.ps1` script will pull code, migrate DB, build frontend, and restart PM2 (`pm2 reload all`).
