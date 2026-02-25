CREATE TABLE IF NOT EXISTS searches (
    id VARCHAR(36) PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'reddit',
    requested_limit INTEGER NOT NULL,
    fetched_count INTEGER NOT NULL DEFAULT 0,
    analyzed_count INTEGER NOT NULL DEFAULT 0,
    positive_count INTEGER NOT NULL DEFAULT 0,
    neutral_count INTEGER NOT NULL DEFAULT 0,
    negative_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sentiment_results (
    id VARCHAR(36) PRIMARY KEY,
    search_id VARCHAR(36) NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
    source_post_id VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'reddit',
    author VARCHAR(100),
    subreddit VARCHAR(100),
    title TEXT,
    body TEXT,
    permalink TEXT,
    posted_at TIMESTAMPTZ,
    neg_score NUMERIC(5,4) NOT NULL,
    neu_score NUMERIC(5,4) NOT NULL,
    pos_score NUMERIC(5,4) NOT NULL,
    compound_score NUMERIC(6,4) NOT NULL,
    sentiment_label VARCHAR(10) NOT NULL CHECK (sentiment_label IN ('positive', 'neutral', 'negative')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_searches_keyword_created_at
    ON searches (keyword, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_sentiment_results_search_id
    ON sentiment_results (search_id);

CREATE INDEX IF NOT EXISTS idx_sentiment_results_sentiment_label
    ON sentiment_results (sentiment_label);
