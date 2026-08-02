# Security Design

## 1. Authentication & Authorization
- **Method**: JWT (JSON Web Tokens) with short-lived access tokens and HttpOnly refresh tokens.
- **Roles**:
  - `Admin`: Full access to manage users, data sources, and trigger manual reports.
  - `Researcher`: Access to the AI Gateway chat and deeper analytics.
  - `Viewer`: Read-only access to dashboards and weekly reports.

## 2. API Security
- **Rate Limiting**: Implemented via Redis to prevent abuse.
- **CORS**: Configurable via environment variables. Must explicitly allow the frontend domain/IP.
- **Data Validation**: Strict Pydantic schemas enforce type safety and prevent injection attacks.

## 3. Secret Management
- **AI Gateway**: The OpenRouter API key is strictly stored in the Backend's `.env` file and is never exposed to the Frontend.
- **Database**: PostgreSQL passwords and Redis connections are stored as environment variables.

## 4. Audit & Provenance
- All mutations (creating users, editing sources) are logged in the `audit_logs` table.
- Raw JSON from data ingestion is preserved for auditing algorithms.
