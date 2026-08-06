# Project Rules & Guidelines

## 1. No Docker Policy
- The system must be fully runnable without Docker.
- Environment setup is handled via `setup.ps1` for dependencies and `PM2` for process management.
- Python dependencies must be managed via standard `requirements.txt` or `uv`/`pip`.
- Node dependencies via `npm`.

## 2. API Design & Security
- All APIs must reside under `/api/v1/`.
- The Frontend MUST NEVER have access to the OpenRouter API Key. All LLM calls route through the Backend's AI Gateway.
- Strict Pydantic v2 schemas must validate all incoming and outgoing API data.

## 3. Data Ingestion Standards
- Never silently discard failed data. Always log failures and support reprocessing.
- Prefer official APIs over web scraping.
- Maintain source URLs and original timestamps for provenance.
- Ingestion jobs must be idempotent.

## 4. Coding Standards
- Python: PEP-8 compliant, use Type Hints aggressively.
- TypeScript: Strict mode enabled, avoid `any`.
- UI: Use Tailwind and shadcn/ui. Do not invent custom CSS unless absolutely necessary.

## 5. Branching & Milestones
- Development will strictly follow the independently testable milestones defined in the roadmap.
- Every major feature must have accompanying Pytest tests.
