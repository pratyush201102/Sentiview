---
title: Sentiview Midterm Progress Report
subtitle: CSCI 411/412 Senior Seminar II (Weeks 1–8)
author: Pratyush Raj Dulal
date: March 13, 2026
course: CSCI 411/412 Senior Seminar II
instructor: Dr. Qi Li
---

# 1. Introduction

This midterm report summarizes the technical progress of **Sentiview**, a social media sentiment analysis system focused on Reddit data ingestion, sentiment classification, and dashboard-based insight delivery. The project objective remains to provide an accessible, open-source platform for tracking public opinion trends.

This submission covers implementation status through **Week 8**, including backend completion and implemented frontend/dashboard development.

---

# 2. Focused Requirements

## 2.1 Current Progress

### A. Implementation Status

### Completed (Weeks 1–6: Backend Core)
- FastAPI backend and modular project architecture established.
- PostgreSQL schema implemented with `searches` and `sentiment_results` tables.
- Reddit ingestion client implemented using Reddit public JSON endpoint.
- VADER sentiment analysis service implemented and integrated.
- API endpoints completed:
  - `POST /api/v1/analyze`
  - `GET /api/v1/searches`
  - `GET /api/v1/searches/{search_id}`
  - `GET /api/v1/searches/{search_id}/export.csv`
- Unit tests added for sentiment classification logic.
- Docker-based local development workflow established.

### Completed (Weeks 7–8: Frontend + Visualization)
- Frontend dashboard implemented in `frontend/index.html`, `frontend/styles.css`, and `frontend/app.js`.
- Dashboard layout delivered with:
   1. Query/Input panel
   2. Summary metrics panel
   3. Visualization panel
   4. Search history table
- **Chart.js integrated** for:
   - Enhanced doughnut chart for sentiment distribution (center total + percentage tooltips)
   - Stacked trend chart for recent searches (clearer comparisons across positive/neutral/negative)
- Full frontend-to-backend binding completed for:
   - `POST /api/v1/analyze`
   - `GET /api/v1/searches`
   - `GET /api/v1/searches/{search_id}`
   - `GET /api/v1/searches/{search_id}/export.csv`
- Backend CORS middleware enabled for local browser-based frontend development.
- API health endpoint enhanced to include database status (`up`/`down`) for startup diagnostics.
- Error handling improved to return actionable HTTP responses for database and Reddit API failures.
- Docker/PostgreSQL setup hardened by moving project DB mapping to port `5433` to avoid local PostgreSQL conflicts.

### In Progress at Week 8 Boundary
- UI polish and small interaction refinements for presentation quality.
- Expanded integration testing across varied keyword datasets.

### B. GitHub Repository (Central Record)
Repository URL: **https://github.com/pratyushrajdulal/sentiview**

The repository serves as the central source for:
- Source code (backend + dashboard development artifacts)
- Setup and run instructions in `README.md`
- API and architecture documentation in `docs/`
- Progress reports and development logs

### C. Development Timeline Comparison (Proposal vs Current)

| Timeline Item (Original Plan) | Target | Current Status (Midterm) |
|---|---|---|
| Project setup and architecture | Weeks 1–2 | Completed on schedule |
| Database + backend API + sentiment pipeline | Weeks 3–6 | Completed on schedule |
| Frontend dashboard + visualization integration | Weeks 7–8 | Completed (functional dashboard + Chart.js integration) |
| Integrated demo-ready full stack | Week 9+ | In progress, on track with minor integration risk |

**Summary:** The project is aligned with the original schedule. Backend milestones were met, and Week 7–8 frontend/dashboard milestones were implemented with working API integration.

---

## 2.2 Challenges and Proposal Adjustments

### A. Technical Difficulties

1. **Sentiment Library Environment Issue (NLTK Runtime Downloads)**
   - **Issue:** NLTK VADER dependency required runtime lexicon download, which caused SSL-related failures in development/testing.
   - **Resolution:** Replaced NLTK-based setup with `vaderSentiment` package (bundled lexicon), improving reliability.

2. **Data Type Consistency Across DB and API Layers**
   - **Issue:** UUID handling inconsistencies between ORM/database/API serialization created risk of type mismatch.
   - **Resolution:** Standardized IDs as string UUID format (`VARCHAR(36)`), simplifying serialization and reducing conversion complexity.

3. **Frontend Visualization Integration Complexity**
   - **Issue:** Backend outputs are record-oriented while charts need aggregated/grouped series.
   - **Resolution:** Defined transformation logic from API payloads to Chart.js datasets, then upgraded chart design to an enhanced doughnut view and stacked trend view with improved tooltip readability.

4. **Source Data Quality Variability (Reddit Content)**
   - **Issue:** Some fetched posts have empty or low-information content, which affects sentiment quality.
   - **Resolution:** Added filtering/guardrails in analysis workflow and counted analyzed vs fetched items explicitly.

5. **Local Database Port Conflict During Integration**
   - **Issue:** Host port `5432` pointed to a non-project PostgreSQL service in local setup, causing database role mismatch and failed analysis requests.
   - **Resolution:** Updated Docker mapping and configuration defaults to use port `5433`, added database-aware health reporting, and improved API error messages for faster troubleshooting.

### B. Strategic Adjustments

- **No major scope reduction is requested at midterm.**
- The proposal remains technically rigorous and feasible.
- Adjustment made: prioritize a robust, integrated MVP (ingestion → sentiment → dashboard) before advanced features (forecasting, multi-source expansion).

If additional scope change becomes necessary after integration testing, a modified proposal will be submitted per course policy.

---

## 2.3 Demonstration of Work Done

### A. Preliminary Results

- Backend is operational and returns sentiment-labeled outputs with aggregate counts.
- Example runs demonstrate successful classification into positive/neutral/negative categories.
- Search history and CSV export are functional, confirming persistence and retrieval pipeline readiness.
- Preliminary dashboard work demonstrates the intended UI flow from query input to chart rendering with transformed sentiment data.

### B. Technical Demo Status

For midterm presentation, demonstration includes:
1. Submit keyword query to backend analysis endpoint.
2. Display returned aggregate sentiment metrics.
3. Render enhanced Chart.js visualizations (doughnut distribution with center totals and stacked sentiment trend chart) from live API data.
4. Export analyzed results as CSV.

**Current demo readiness:** Core backend and frontend dashboard workflows are operational for a live functional demo.

---

## 2.4 Future Plan for Final Delivery

### A. Technical Milestones (Second Half)

### Weeks 9–10 (Integration and Stability)
- Complete frontend-backend endpoint binding.
- Finalize Chart.js visualizations (distribution + trend views).
- Implement loading/error/empty-state UX.
- Perform end-to-end testing with representative datasets.

### Weeks 11–12 (Quality and Feature Completion)
- Improve dashboard usability and responsiveness.
- Expand tests (API integration + key UI flows).
- Optimize query/transform performance for larger result sets.
- Refine documentation for deployment and usage.

### Weeks 13–14 (Final Packaging)
- Final bug fixes and system polish.
- Final report writing and technical reflection.
- GitHub cleanup: structure, README updates, reproducibility checks.
- Prepare and record final video demonstration.

### B. Final Deliverables Plan

1. **Final Written Report**
   - Architecture evolution, implementation details, results, limitations, and future work.

2. **Polished GitHub Repository**
   - Clean folder structure, clear setup instructions, test instructions, and demo walkthrough.

3. **Final Video Presentation**
   - End-to-end demonstration of the full pipeline from keyword search to sentiment visualization and data export.

---

# 3. Professional Conduct and Integrity

All work presented reflects my project implementation effort and course-aligned development process.

Open-source tools/libraries used include (not limited to):
- FastAPI
- SQLAlchemy
- PostgreSQL
- vaderSentiment
- httpx
- Chart.js (for dashboard visualization phase)

AI assistance was used for writing support, structuring documentation, and development productivity. All code decisions, integration, debugging, and validation were completed under my supervision and responsibility.

---

# 4. Midterm Summary

By Week 8, Sentiview has a completed backend sentiment analysis pipeline and an operational frontend dashboard with refined visualizations. The project is on track for final delivery, with remaining work focused on integration testing depth, UX polishing, and final presentation packaging.

**Repository:** https://github.com/pratyushrajdulal/sentiview
