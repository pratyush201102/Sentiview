# Sentiview

Sentiview is a social media sentiment analysis project with a FastAPI backend, PostgreSQL storage, and a frontend dashboard that visualizes sentiment using Chart.js.

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
   - `psql postgresql://postgres:postgres@localhost:5433/sentiview -f backend/sql/schema.sql`
6. Start API:
   - `uvicorn backend.app.main:app --reload --port 8000`

Once running, access the API documentation at `http://localhost:8000/docs`

## API Endpoints
- `GET /health` — service health check.
- `POST /api/v1/analyze` — fetch posts for a keyword, run sentiment analysis, persist results.
- `GET /api/v1/searches` — list past searches with aggregate counts.
- `GET /api/v1/searches/{search_id}` — detailed results for one search.
- `GET /api/v1/searches/{search_id}/export.csv` — export search results as CSV.

## Week 7–8 (Completed in this setup)
- Frontend dashboard added under `frontend/`.
- Dashboard layout includes query form, summary metrics, chart panel, and history table.
- Chart.js integrated for:
   - Pie chart: sentiment distribution (positive/neutral/negative)
   - Line chart: recent search sentiment trend
- Frontend integrated with backend endpoints (`/analyze`, `/searches`, `/searches/{id}`, `/export.csv`).

## Week 9–10 (Optimization & UX)
- Added skeleton loader states in the dashboard for long API operations:
   - Summary metrics shimmer placeholders
   - Chart and history table loading overlays
- Improved mobile responsiveness with tighter breakpoints and single-column behavior:
   - Added Tailwind utility classes to reinforce responsive spacing and typography
   - Form controls stack on small screens
   - Metrics grid adapts from 3 columns to 2 columns to 1 column
   - Chart heights scale down for compact devices
   - Table remains horizontally scrollable on narrow viewports
- Improved frontend-backend integration reliability:
   - Standardized API root resolution for health checks
   - Added request timeout handling for long-running calls
   - Added robust API error parsing for JSON/text error responses

## Frontend Quick Start

1. Start backend API (`uvicorn backend.app.main:app --reload --port 8000`)
2. Serve frontend static files:
    - `cd frontend`
    - `python3 -m http.server 5173`
3. Open `http://localhost:5173`

Default API base in UI: `http://localhost:8000/api/v1`
