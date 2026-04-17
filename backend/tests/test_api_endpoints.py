from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.models import Base, Search, SentimentResult
from backend.app.db.session import get_db
from backend.app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client, TestingSessionLocal

    app.dependency_overrides.clear()


def test_health_endpoint_returns_ok(client):
    test_client, _ = client

    response = test_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] in {"up", "down"}


def test_searches_and_details_endpoints_return_seeded_data(client):
    test_client, session_local = client

    with session_local() as db:
        search = Search(
            keyword="ai",
            source="reddit",
            requested_limit=10,
            fetched_count=3,
            analyzed_count=2,
            positive_count=1,
            neutral_count=1,
            negative_count=0,
        )
        db.add(search)
        db.flush()

        db.add(
            SentimentResult(
                search_id=search.id,
                source_post_id="post-1",
                source="reddit",
                author="alice",
                subreddit="technology",
                title="AI release",
                body="looks good",
                permalink="https://reddit.com/r/technology/post-1",
                posted_at=datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc),
                neg_score=Decimal("0.0000"),
                neu_score=Decimal("0.7000"),
                pos_score=Decimal("0.3000"),
                compound_score=Decimal("0.6124"),
                sentiment_label="positive",
            )
        )
        db.commit()
        search_id = search.id

    list_response = test_client.get("/api/v1/searches")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert list_payload["items"][0]["id"] == search_id

    detail_response = test_client.get(f"/api/v1/searches/{search_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["search"]["id"] == search_id
    assert len(detail_payload["results"]) == 1


def test_export_csv_supports_column_filtering(client):
    test_client, session_local = client

    with session_local() as db:
        search = Search(
            keyword="metrics",
            source="reddit",
            requested_limit=5,
            fetched_count=1,
            analyzed_count=1,
            positive_count=1,
            neutral_count=0,
            negative_count=0,
        )
        db.add(search)
        db.flush()
        db.add(
            SentimentResult(
                search_id=search.id,
                source_post_id="post-2",
                source="reddit",
                author="bob",
                subreddit="datascience",
                title="Great benchmark",
                body="benchmark looks strong",
                permalink="https://reddit.com/r/datascience/post-2",
                posted_at=datetime(2026, 4, 1, 12, 30, tzinfo=timezone.utc),
                neg_score=Decimal("0.0000"),
                neu_score=Decimal("0.3000"),
                pos_score=Decimal("0.7000"),
                compound_score=Decimal("0.8402"),
                sentiment_label="positive",
            )
        )
        db.commit()
        search_id = search.id

    response = test_client.get(
        f"/api/v1/searches/{search_id}/export.csv?columns=source_post_id,title,sentiment_label"
    )

    assert response.status_code == 200
    csv_text = response.content.decode("utf-8-sig")
    assert "source_post_id,title,sentiment_label" in csv_text
    assert "post-2,Great benchmark,positive" in csv_text


def test_export_csv_rejects_invalid_columns(client):
    test_client, session_local = client

    with session_local() as db:
        search = Search(
            keyword="validation",
            source="reddit",
            requested_limit=1,
            fetched_count=1,
            analyzed_count=1,
            positive_count=0,
            neutral_count=1,
            negative_count=0,
        )
        db.add(search)
        db.commit()
        search_id = search.id

    response = test_client.get(f"/api/v1/searches/{search_id}/export.csv?columns=bad_column")

    assert response.status_code == 400
    assert "Invalid CSV columns" in response.json()["detail"]
