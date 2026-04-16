import csv
import io
import logging
import re
from datetime import datetime, timezone
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from backend.app.db.models import Search, SentimentResult
from backend.app.db.session import get_db
from backend.app.schemas import AnalyzeRequest, AnalyzeResponse, SearchListResponse, SearchSummary, SentimentItem
from backend.app.services.reddit_client import RedditClient
from backend.app.services.sentiment import SentimentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["sentiment"])

CSV_EXPORT_COLUMN_ORDER = [
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


def _sanitize_csv_cell(value: object) -> str:
    """Prevent spreadsheet formula injection while preserving text content."""
    if value is None:
        return ""

    text = str(value)
    if text and text[0] in ("=", "+", "-", "@"):
        return f"'{text}"
    return text


def _safe_filename_fragment(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip())
    normalized = normalized.strip("-")
    return normalized[:48] or "search"


def _parse_csv_columns(columns: list[str] | None) -> list[str]:
    """Parse and validate requested CSV columns from query params."""
    if not columns:
        return CSV_EXPORT_COLUMN_ORDER[:]

    parsed_columns: list[str] = []
    seen: set[str] = set()

    for raw_value in columns:
        for column in raw_value.split(","):
            candidate = column.strip()
            if not candidate:
                continue
            if candidate not in seen:
                parsed_columns.append(candidate)
                seen.add(candidate)

    if not parsed_columns:
        raise HTTPException(status_code=400, detail="At least one valid CSV column must be provided.")

    invalid_columns = [column for column in parsed_columns if column not in CSV_EXPORT_COLUMN_ORDER]
    if invalid_columns:
        allowed_columns = ", ".join(CSV_EXPORT_COLUMN_ORDER)
        invalid_values = ", ".join(invalid_columns)
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid CSV columns: {invalid_values}. "
                f"Allowed columns are: {allowed_columns}."
            ),
        )

    return [column for column in CSV_EXPORT_COLUMN_ORDER if column in seen]


def _csv_value_for_column(row: SentimentResult, column: str) -> str | float:
    if column == "source_post_id":
        return _sanitize_csv_cell(row.source_post_id)
    if column == "author":
        return _sanitize_csv_cell(row.author)
    if column == "subreddit":
        return _sanitize_csv_cell(row.subreddit)
    if column == "title":
        return _sanitize_csv_cell(row.title)
    if column == "body":
        return _sanitize_csv_cell(row.body)
    if column == "permalink":
        return _sanitize_csv_cell(row.permalink)
    if column == "posted_at":
        return row.posted_at.isoformat() if row.posted_at else ""
    if column == "neg_score":
        return float(row.neg_score)
    if column == "neu_score":
        return float(row.neu_score)
    if column == "pos_score":
        return float(row.pos_score)
    if column == "compound_score":
        return float(row.compound_score)
    if column == "sentiment_label":
        return row.sentiment_label

    raise ValueError(f"Unexpected CSV column: {column}")


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_keyword(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Analyze sentiment for Reddit posts matching a keyword.
    
    Fetches posts from Reddit, runs VADER sentiment analysis, and persists results.
    
    Args:
        payload: AnalyzeRequest containing keyword, limit, and source
        db: Database session dependency
        
    Returns:
        AnalyzeResponse with search metadata and sentiment results
        
    Raises:
        HTTPException: If source is not 'reddit' or if Reddit API/database errors occur
    """
    if payload.source.lower() != "reddit":
        logger.warning(f"Unsupported source requested: {payload.source}")
        raise HTTPException(status_code=400, detail="Only 'reddit' source is supported in this phase.")

    try:
        logger.info(f"Processing analyze request for keyword: {payload.keyword}")
        
        reddit_client = RedditClient()
        sentiment_service = SentimentService()

        raw_posts = reddit_client.search_posts(payload.keyword, payload.limit)
        logger.info(f"Fetched {len(raw_posts)} posts from Reddit")

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

        logger.info(f"Analysis complete: {len(stored_results)} results stored (positive: {positive_count}, neutral: {neutral_count}, negative: {negative_count})")

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
        
    except httpx.HTTPError as e:
        logger.error(f"Reddit API request failed: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=502, detail="Failed to fetch data from Reddit API")
    except OperationalError as e:
        logger.error(f"Database connection error during analysis: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Verify DATABASE_URL and ensure PostgreSQL is running.",
        )
    except Exception as e:
        logger.error(f"Error during sentiment analysis: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error during analysis")


@router.get("/searches", response_model=SearchListResponse)
def list_searches(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    Retrieve list of recent searches with pagination support.
    
    Returns searches ordered by creation time (newest first) with configurable pagination.
    
    Args:
        skip: Number of results to skip (default: 0, minimum: 0)
        limit: Number of results per page (default: 20, minimum: 1, maximum: 100)
        db: Database session dependency
        
    Returns:
        Paginated search history payload with metadata
    """
    # Validate pagination parameters
    skip = max(0, skip)
    limit = min(100, max(1, limit))
    
    try:
        logger.debug(f"Fetching searches with skip={skip}, limit={limit}")
        total = db.query(Search).count()
        rows = db.query(Search).order_by(desc(Search.created_at)).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(rows)} searches (skip={skip}, limit={limit})")

        items = [
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

        return SearchListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total,
        )
    except OperationalError as e:
        logger.error(f"Database connection error retrieving searches: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Verify DATABASE_URL and ensure PostgreSQL is running.",
        )
    except Exception as e:
        logger.error(f"Error retrieving searches: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving search history")


@router.get("/searches/{search_id}", response_model=AnalyzeResponse)
def get_search(search_id: str, db: Session = Depends(get_db)):
    """
    Retrieve detailed results for a specific search.
    
    Args:
        search_id: UUID of the search to retrieve
        db: Database session dependency
        
    Returns:
        AnalyzeResponse with search metadata and all sentiment results
        
    Raises:
        HTTPException: 404 if search not found
    """
    try:
        logger.debug(f"Retrieving search: {search_id}")
        search = db.query(Search).filter(Search.id == search_id).first()
        if not search:
            logger.warning(f"Search not found: {search_id}")
            raise HTTPException(status_code=404, detail="Search not found")

        rows = db.query(SentimentResult).filter(SentimentResult.search_id == search_id).all()
        logger.info(f"Retrieved {len(rows)} results for search {search_id}")

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
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error retrieving search {search_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Verify DATABASE_URL and ensure PostgreSQL is running.",
        )
    except Exception as e:
        logger.error(f"Error retrieving search {search_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving search")


@router.get("/searches/{search_id}/export.csv")
def export_search_csv(
    search_id: str,
    columns: list[str] | None = Query(
        default=None,
        description=(
            "Optional columns to include in CSV export. "
            "Use comma-separated values or repeat the columns query parameter."
        ),
        examples=["source_post_id,title,sentiment_label"],
    ),
    db: Session = Depends(get_db),
):
    """
    Export search results as CSV file.
    
    Args:
        search_id: UUID of the search to export
        db: Database session dependency
        
    Returns:
        StreamingResponse with CSV data
        
    Raises:
        HTTPException: 404 if search not found
    """
    try:
        logger.debug(f"Exporting CSV for search: {search_id}")
        selected_columns = _parse_csv_columns(columns)

        search = db.query(Search).filter(Search.id == search_id).first()
        if not search:
            logger.warning(f"Search not found for export: {search_id}")
            raise HTTPException(status_code=404, detail="Search not found")

        rows = db.query(SentimentResult).filter(SentimentResult.search_id == search_id).all()

        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["exported_at_utc", datetime.now(timezone.utc).isoformat()])
        writer.writerow(["search_id", str(search.id)])
        writer.writerow(["keyword", _sanitize_csv_cell(search.keyword)])
        writer.writerow(["source", search.source])
        writer.writerow(["requested_limit", search.requested_limit])
        writer.writerow(["fetched_count", search.fetched_count])
        writer.writerow(["analyzed_count", search.analyzed_count])
        writer.writerow([])
        writer.writerow(selected_columns)

        for row in rows:
            writer.writerow([_csv_value_for_column(row, column) for column in selected_columns])

        output.seek(0)
        csv_content = output.getvalue().encode("utf-8-sig")
        logger.info(f"CSV export generated for search {search_id} with {len(rows)} rows")

        keyword_fragment = _safe_filename_fragment(search.keyword)
        timestamp_fragment = search.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"sentiview_{keyword_fragment}_{timestamp_fragment}.csv"
        content_disposition = (
            f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quote(filename)}"
        )

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": content_disposition},
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error exporting CSV for search {search_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Verify DATABASE_URL and ensure PostgreSQL is running.",
        )
    except Exception as e:
        logger.error(f"Error exporting CSV for search {search_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating CSV export")
