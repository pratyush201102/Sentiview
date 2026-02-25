import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.db.models import Search, SentimentResult
from backend.app.db.session import get_db
from backend.app.schemas import AnalyzeRequest, AnalyzeResponse, SearchSummary, SentimentItem
from backend.app.services.reddit_client import RedditClient
from backend.app.services.sentiment import SentimentService


router = APIRouter(prefix="/api/v1", tags=["sentiment"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_keyword(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    if payload.source.lower() != "reddit":
        raise HTTPException(status_code=400, detail="Only 'reddit' source is supported in this phase.")

    reddit_client = RedditClient()
    sentiment_service = SentimentService()

    raw_posts = reddit_client.search_posts(payload.keyword, payload.limit)

    search = Search(
        keyword=payload.keyword,
        source=payload.source.lower(),
        requested_limit=payload.limit,
        fetched_count=len(raw_posts),
    )
    db.add(search)
    db.flush()

    positive_count = 0
    neutral_count = 0
    negative_count = 0

    stored_results: list[SentimentResult] = []

    for post in raw_posts:
        combined_text = f"{post.get('title', '')}\n{post.get('body', '')}".strip()
        if not combined_text:
            continue

        scores = sentiment_service.score_text(combined_text)
        label = scores["sentiment_label"]
        if label == "positive":
            positive_count += 1
        elif label == "negative":
            negative_count += 1
        else:
            neutral_count += 1

        item = SentimentResult(
            search_id=search.id,
            source_post_id=post["source_post_id"],
            source="reddit",
            author=post.get("author"),
            subreddit=post.get("subreddit"),
            title=post.get("title"),
            body=post.get("body"),
            permalink=post.get("permalink"),
            posted_at=post.get("posted_at"),
            neg_score=scores["neg_score"],
            neu_score=scores["neu_score"],
            pos_score=scores["pos_score"],
            compound_score=scores["compound_score"],
            sentiment_label=label,
        )
        db.add(item)
        stored_results.append(item)

    search.analyzed_count = len(stored_results)
    search.positive_count = positive_count
    search.neutral_count = neutral_count
    search.negative_count = negative_count

    db.commit()
    db.refresh(search)
    for item in stored_results:
        db.refresh(item)

    summary = SearchSummary(
        id=search.id,
        keyword=search.keyword,
        source=search.source,
        requested_limit=search.requested_limit,
        fetched_count=search.fetched_count,
        analyzed_count=search.analyzed_count,
        positive_count=search.positive_count,
        neutral_count=search.neutral_count,
        negative_count=search.negative_count,
        created_at=search.created_at,
    )
    results = [
        SentimentItem(
            id=row.id,
            source_post_id=row.source_post_id,
            author=row.author,
            subreddit=row.subreddit,
            title=row.title,
            body=row.body,
            permalink=row.permalink,
            posted_at=row.posted_at,
            neg_score=float(row.neg_score),
            neu_score=float(row.neu_score),
            pos_score=float(row.pos_score),
            compound_score=float(row.compound_score),
            sentiment_label=row.sentiment_label,
        )
        for row in stored_results
    ]

    return AnalyzeResponse(search=summary, results=results)


@router.get("/searches", response_model=list[SearchSummary])
def list_searches(db: Session = Depends(get_db)):
    rows = db.query(Search).order_by(desc(Search.created_at)).limit(100).all()
    return [
        SearchSummary(
            id=row.id,
            keyword=row.keyword,
            source=row.source,
            requested_limit=row.requested_limit,
            fetched_count=row.fetched_count,
            analyzed_count=row.analyzed_count,
            positive_count=row.positive_count,
            neutral_count=row.neutral_count,
            negative_count=row.negative_count,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/searches/{search_id}", response_model=AnalyzeResponse)
def get_search(search_id: str, db: Session = Depends(get_db)):
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")

    rows = db.query(SentimentResult).filter(SentimentResult.search_id == search_id).all()

    return AnalyzeResponse(
        search=SearchSummary(
            id=search.id,
            keyword=search.keyword,
            source=search.source,
            requested_limit=search.requested_limit,
            fetched_count=search.fetched_count,
            analyzed_count=search.analyzed_count,
            positive_count=search.positive_count,
            neutral_count=search.neutral_count,
            negative_count=search.negative_count,
            created_at=search.created_at,
        ),
        results=[
            SentimentItem(
                id=row.id,
                source_post_id=row.source_post_id,
                author=row.author,
                subreddit=row.subreddit,
                title=row.title,
                body=row.body,
                permalink=row.permalink,
                posted_at=row.posted_at,
                neg_score=float(row.neg_score),
                neu_score=float(row.neu_score),
                pos_score=float(row.pos_score),
                compound_score=float(row.compound_score),
                sentiment_label=row.sentiment_label,
            )
            for row in rows
        ],
    )


@router.get("/searches/{search_id}/export.csv")
def export_search_csv(search_id: str, db: Session = Depends(get_db)):
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")

    rows = db.query(SentimentResult).filter(SentimentResult.search_id == search_id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "source_post_id",
            "author",
            "subreddit",
            "title",
            "body",
            "permalink",
            "posted_at",
            "neg_score",
            "neu_score",
            "pos_score",
            "compound_score",
            "sentiment_label",
        ]
    )

    for row in rows:
        writer.writerow(
            [
                row.source_post_id,
                row.author,
                row.subreddit,
                row.title,
                row.body,
                row.permalink,
                row.posted_at.isoformat() if row.posted_at else "",
                float(row.neg_score),
                float(row.neu_score),
                float(row.pos_score),
                float(row.compound_score),
                row.sentiment_label,
            ]
        )

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=search_{search_id}.csv"},
    )
