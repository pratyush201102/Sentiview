# Sentiview

Sentiview is a real-time social media sentiment analysis backend focused on Reddit content ingestion, NLP sentiment scoring, and API-first delivery for dashboard visualization.

## Week 1–2 (Completed in this setup)
- Project scope finalized with a backend-first MVP.
- GitHub-ready repository structure initialized.
- Local development environment setup (FastAPI + PostgreSQL + Docker Compose).

## Week 3–4 (Completed in this setup)
- Modular system architecture documented.
- PostgreSQL schema designed and provided.
- NLP library finalized: **VADER (NLTK)** for baseline sentiment analysis.

## Week 5–6 (Completed in this setup)
- FastAPI backend implemented.
- Reddit ingestion logic implemented via public Reddit JSON API.
- Initial sentiment processing pipeline implemented and persisted.

## Quick Start

### Automated Startup (Recommended)
Simply run the startup script from the project directory:
```bash
./start.sh
```

This will:
- Activate your virtual environment
- Setup environment variables
- Start PostgreSQL (if available)
- Initialize the database schema
- Launch the FastAPI server with hot-reload
- Automatically open the API docs in your browser

### Manual Setup
If you prefer manual setup or the script doesn't work:

1. Create and activate a virtual environment:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
2. Install dependencies:
   - `pip install -r backend/requirements.txt`
3. Copy env file:
   - `cp .env.example .env`
4. Start PostgreSQL:
   - `docker compose up -d`
5. Create schema:
   - `psql postgresql://postgres:postgres@localhost:5432/sentiview -f backend/sql/schema.sql`
6. Start API:
   - `uvicorn backend.app.main:app --reload --port 8000`

Once running, access the API documentation at `http://localhost:8000/docs`

## API Endpoints
- `GET /health` — service health check.
- `POST /api/v1/analyze` — fetch posts for a keyword, run sentiment analysis, persist results.
- `GET /api/v1/searches` — list past searches with aggregate counts.
- `GET /api/v1/searches/{search_id}` — detailed results for one search.
- `GET /api/v1/searches/{search_id}/export.csv` — export search results as CSV.

## Suggested Next Step (Week 7–8)
Build the React dashboard to consume these endpoints for pie and line charts.
