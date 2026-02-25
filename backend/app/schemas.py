from datetime import datetime

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    keyword: str = Field(min_length=2, max_length=255)
    source: str = Field(default="reddit")
    limit: int = Field(default=25, ge=1, le=100)


class SentimentItem(BaseModel):
    id: str
    source_post_id: str
    author: str | None
    subreddit: str | None
    title: str | None
    body: str | None
    permalink: str | None
    posted_at: datetime | None
    neg_score: float
    neu_score: float
    pos_score: float
    compound_score: float
    sentiment_label: str


class SearchSummary(BaseModel):
    id: str
    keyword: str
    source: str
    requested_limit: int
    fetched_count: int
    analyzed_count: int
    positive_count: int
    neutral_count: int
    negative_count: int
    created_at: datetime


class AnalyzeResponse(BaseModel):
    search: SearchSummary
    results: list[SentimentItem]
