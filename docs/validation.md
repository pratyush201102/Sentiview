# Validation and Quality Assurance

## 1. Sentiment Accuracy Manual Audit

This project uses VADER for baseline sentiment scoring. To quantify model quality against human perception, run a manual audit over a 100-post sample.

### Input format
Prepare a CSV file with at least 100 rows and these columns:

- `text`: post content used for scoring
- `human_label`: one of `positive`, `neutral`, `negative`

Reference template: `backend/audit/sample_manual_audit.csv`

### Run audit

```bash
python -m backend.tools.sentiment_audit --input backend/audit/manual_audit_100.csv
```

Optional custom output path:

```bash
python -m backend.tools.sentiment_audit --input backend/audit/manual_audit_100.csv --output backend/audit/final_report.json
```

### Report output
The generated JSON includes:

- sample size
- accuracy
- macro precision / recall / F1
- per-label precision / recall / F1 / support
- confusion matrix

These metrics can be used directly in the final report section for model validation.

## 2. Automated Integration Testing

Endpoint-level integration tests are included in `backend/tests/test_api_endpoints.py`.

### Run

```bash
pytest backend/tests -q
```

### Coverage focus

- service health endpoint
- search listing and detail retrieval
- CSV export flow with selected columns
- CSV export validation for unsupported columns

## 3. Full Stack Developer Startup

For one-command local setup and launch:

```bash
./start.sh
```

This starts:

- PostgreSQL via Docker (if available)
- FastAPI backend on `http://localhost:8000`
- Frontend static server on `http://localhost:5173`

This allows developers to clone and run the full stack immediately.
