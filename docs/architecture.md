# Sentiview Architecture (Week 3–4)

## Overview
Sentiview uses a modular pipeline architecture with clear separation of concerns:

1. **Data Collection Layer**
   - Fetches Reddit posts by keyword from the public Reddit JSON endpoint.
   - Isolates source-specific logic in a client service.

2. **NLP Pipeline Layer**
   - Preprocesses text by combining title + body.
   - Uses VADER (NLTK) to compute polarity scores.
   - Produces sentiment class labels: Positive, Neutral, Negative.

3. **Storage Layer**
   - PostgreSQL stores:
     - Search metadata (`searches`)
     - Post-level sentiment results (`sentiment_results`)

4. **Presentation Layer**
   - FastAPI REST API serves search execution, historical retrieval, and CSV export.

## Data Flow
1. Client submits keyword and fetch parameters.
2. API creates a `searches` row.
3. Reddit client fetches posts.
4. Sentiment service scores each post.
5. API stores row-level sentiment data in `sentiment_results`.
6. API returns aggregate and detailed response to frontend.

## Why VADER
VADER is selected as the initial NLP baseline because:
- It is fast and lightweight for iterative development.
- It performs reasonably well for social-media style text.
- It provides interpretable polarity scores (`neg`, `neu`, `pos`, `compound`).

## Extensibility Path
- Add optional sources (YouTube comments, product review APIs).
- Replace or complement VADER with transformer-based models.
- Introduce asynchronous workers for high-volume ingestion.
- Add caching and rate-limit handling.
