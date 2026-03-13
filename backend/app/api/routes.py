import csv
import io
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from backend.app.db.models import Search, SentimentResult
from backend.app.db.session import get_db
from backend.app.schemas import AnalyzeRequest, AnalyzeResponse, SearchSummary, SentimentItem
from backend.app.services.reddit_client import RedditClient
from backend.app.services.sentiment import SentimentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["sentiment"])


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


@router.get("/searches", response_model=list[SearchSummary])
def list_searches(db: Session = Depends(get_db)):
    """
    Retrieve list of recent searches with aggregate sentiment counts.
    
    Returns the 100 most recent searches ordered by creation time.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of SearchSummary objects
    """
    try:
        logger.debug("Fetching recent searches")
        rows = db.query(Search).order_by(desc(Search.created_at)).limit(100).all()
        logger.info(f"Retrieved {len(rows)} searches")
        
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
def export_search_csv(search_id: str, db: Session = Depends(get_db)):
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
        search = db.query(Search).filter(Search.id == search_id).first()
        if not search:
            logger.warning(f"Search not found for export: {search_id}")
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
        logger.info(f"CSV export generated for search {search_id} with {len(rows)} rows")

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=search_{search_id}.csv"},
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
