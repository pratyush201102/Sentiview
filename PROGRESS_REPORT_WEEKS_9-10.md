# Project Progress Report (Weeks 9-10)

GitHub Repository: <ADD_YOUR_GITHUB_REPO_LINK_HERE>

Course: <COURSE_NAME>
Student: <YOUR_NAME>
Date: March 2026

## 1. Project Overview and Current Status

Sentiview is a sentiment analysis dashboard that collects Reddit posts by keyword, scores text sentiment using VADER, stores results in PostgreSQL, and visualizes outcomes in a web dashboard.

Problem addressed:
- Manual social sentiment tracking is slow and inconsistent.
- Sentiview provides faster keyword-level sentiment summaries and trend visibility.

Intended users:
- Students and researchers monitoring topic sentiment.
- Early-stage product/marketing teams tracking public response themes.

Current development stage:
- Core ingestion, scoring, storage, and dashboard analytics are complete.
- Weeks 9-10 work focused on UX polishing and frontend-backend reliability.

## 2. Design Illustrations

Use existing diagrams from docs and include each with a caption:

1. System architecture diagram
- File: docs/ARCHITECTURE_DIAGRAM.md
- Explanation: Shows frontend, API, sentiment service, and PostgreSQL interactions.

2. Data flow diagram
- File: docs/DATA_FLOW_DIAGRAM.md
- Explanation: Shows request lifecycle from keyword input to chart/table rendering.

3. Database schema diagram
- File: docs/DATABASE_SCHEMA_DIAGRAM.md
- Explanation: Shows Search and SentimentResult entities and relationship design.

4. UI screenshot (Week 9-10 updated dashboard)
- Include screenshots for desktop and mobile view.
- Explanation: Demonstrates skeleton loading states and responsive layout behavior.

## 3. Implementation and Sample Code

### A. Skeleton loaders during long API calls (frontend)
Purpose:
- Provide clear feedback while requests are pending.

Implementation summary:
- Added global loading state toggles in frontend/app.js.
- Added shimmer placeholder styles and loading overlays in frontend/styles.css.
- Applied loading classes to summary metrics, chart cards, and history table.

Design decision:
- Reused class-based loading states instead of extra skeleton HTML nodes for maintainability.

### B. Mobile responsiveness refinement (frontend)
Purpose:
- Improve usability on small screens.

Implementation summary:
- Added Tailwind utility classes for responsive typography, spacing, and layout spans.
- Added tighter breakpoints at 900px and 640px.
- Converted form layout to single-column on small devices.
- Updated metrics grid from 3-column to 2-column to 1-column.
- Reduced chart heights for smaller viewport fit.

Design decision:
- Kept existing CSS architecture and introduced minimal, targeted responsive changes.

### C. Frontend-backend integration reliability (frontend)
Purpose:
- Improve stability and clarity of API interactions.

Implementation summary:
- Added API root normalization for health endpoint calls.
- Added timeout handling using AbortController.
- Added error parsing for JSON and text responses.

Design decision:
- Centralized fetch reliability in one request helper to avoid duplicated edge-case handling.

## 4. GitHub Repository Requirement

Checklist:
- [ ] Create GitHub repository (public or private)
- [ ] Push all source code and docs
- [ ] Add complete README.md
- [ ] Include repository link on first page of report
- [ ] Include screenshot of commit history

Repository structure summary:
- backend/: FastAPI routes, services, DB models, tests
- frontend/: dashboard UI (HTML/CSS/JS + Chart.js)
- docs/: architecture and system design diagrams
- sql/: schema setup

## 5. Initial Results and Testing

Observed results:
- Dashboard now shows loading skeletons during boot, analysis, and search selection.
- Mobile layout remains usable without overlap or clipping on narrow screens.
- API failures now show cleaner error messages; long calls fail with timeout guidance.

Suggested evidence to include:
- Screenshot: dashboard while loading (skeleton visible)
- Screenshot: mobile viewport dashboard
- Screenshot: successful analysis result
- Screenshot: commit history from GitHub

## 6. Challenges and Solutions

Challenge 1: Perceived latency during analysis requests
- Why difficult: sentiment analysis includes external fetch + NLP + database writes.
- Attempted: basic text-only status update.
- Final solution: visual skeleton loaders and disabled action states.

Challenge 2: Mobile readability for dense dashboard cards
- Why difficult: charts, metrics, and table all compete for space.
- Attempted: single breakpoint only.
- Final solution: additional breakpoint and adaptive grid/form/chart sizing.

Challenge 3: Inconsistent error payloads from backend paths
- Why difficult: backend can return JSON detail or plain text errors.
- Final solution: unified error parser in frontend request layer.

## 7. Next Steps

Planned next phase:
- Add filters by date range and subreddit.
- Add pagination/virtualization for larger history tables.
- Add sentiment confidence explanations in UI.
- Expand testing with frontend interaction tests and API contract checks.

Risks:
- Reddit API limits may affect response speed.
- Dashboard complexity may increase render cost as history grows.

Mitigation:
- Add caching and optional background task mode.
- Introduce lazy loading for historical records.

## Submission Notes

- Export this report to PDF after replacing placeholders.
- Ensure GitHub repository link is visible on page 1.
- Add labeled figure captions for every screenshot/diagram.
