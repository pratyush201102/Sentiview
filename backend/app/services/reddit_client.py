import logging
import time
from datetime import datetime, timezone

import httpx

from backend.app.config import settings

logger = logging.getLogger(__name__)


class RedditClient:
    """
    Client for fetching posts from Reddit using the public JSON API.
    
    No OAuth authentication required for public endpoint access.
    Respects rate limiting and includes appropriate User-Agent headers.
    
    Attributes:
        base_url: Reddit API base URL (e.g., https://www.reddit.com)
        user_agent: User-Agent string for API requests
    """
    
    def __init__(self) -> None:
        """Initialize Reddit API client with configured settings."""
        self.base_url = settings.reddit_base_url.rstrip("/")
        self.user_agent = settings.reddit_user_agent
        self.max_retries = max(0, int(settings.reddit_max_retries))
        self.retry_backoff_seconds = max(0.0, float(settings.reddit_retry_backoff_seconds))
        logger.debug(f"RedditClient initialized with base_url: {self.base_url}")

    def search_posts(self, keyword: str, limit: int) -> list[dict]:
        """
        Search Reddit for posts matching a keyword.
        
        Args:
            keyword: Search query term(s)
            limit: Maximum number of posts to fetch (Reddit may return fewer)
            
        Returns:
            List of post dictionaries containing:
                - source_post_id: Reddit post ID
                - author: Post author username
                - subreddit: Subreddit name
                - title: Post title
                - body: Post content/selftext
                - permalink: Full Reddit permalink URL
                - posted_at: Post creation timestamp (UTC)
                
        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If keyword is empty or invalid
        """
        if not keyword or not keyword.strip():
            logger.warning("Empty keyword provided to search_posts")
            raise ValueError("Keyword cannot be empty")

        normalized_keyword = keyword.strip()
            
        if not isinstance(limit, int) or limit <= 0:
            logger.warning(f"Invalid limit provided: {limit}")
            raise ValueError("Limit must be a positive integer")
        
        url = f"{self.base_url}/search.json"
        params = {
            "q": normalized_keyword,
            "sort": "new",
            "limit": limit,
            "restrict_sr": "false",
            "type": "link",
        }
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        try:
            logger.info(f"Fetching Reddit posts for keyword: {normalized_keyword} (limit: {limit})")
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                payload = None
                for attempt in range(self.max_retries + 1):
                    try:
                        response = client.get(url, params=params, headers=headers)
                        response.raise_for_status()
                        payload = response.json()
                        break
                    except httpx.HTTPStatusError as e:
                        status_code = e.response.status_code if e.response is not None else None
                        is_retriable = status_code in {429, 500, 502, 503, 504}
                        if not is_retriable or attempt >= self.max_retries:
                            raise

                        sleep_seconds = self.retry_backoff_seconds * (2 ** attempt)
                        logger.warning(
                            "Transient Reddit API status %s for keyword '%s', retrying in %.2fs (attempt %s/%s)",
                            status_code,
                            normalized_keyword,
                            sleep_seconds,
                            attempt + 1,
                            self.max_retries,
                        )
                        time.sleep(sleep_seconds)
                    except httpx.RequestError as e:
                        if attempt >= self.max_retries:
                            raise

                        sleep_seconds = self.retry_backoff_seconds * (2 ** attempt)
                        logger.warning(
                            "Transient Reddit API request error '%s' for keyword '%s', retrying in %.2fs (attempt %s/%s)",
                            type(e).__name__,
                            normalized_keyword,
                            sleep_seconds,
                            attempt + 1,
                            self.max_retries,
                        )
                        time.sleep(sleep_seconds)

                if payload is None:
                    raise RuntimeError("Reddit API response payload unavailable after retries")
            
            logger.debug(f"Received response from Reddit API for '{normalized_keyword}'")

            children = payload.get("data", {}).get("children", [])
            posts = []
            
            for child in children:
                data = child.get("data", {})
                posts.append(
                    {
                        "source_post_id": data.get("id", ""),
                        "author": data.get("author"),
                        "subreddit": data.get("subreddit"),
                        "title": data.get("title", ""),
                        "body": data.get("selftext", ""),
                        "permalink": f"https://www.reddit.com{data.get('permalink', '')}",
                        "posted_at": datetime.fromtimestamp(data.get("created_utc", 0), tz=timezone.utc)
                        if data.get("created_utc")
                        else None,
                    }
                )

            logger.info(f"Successfully fetched {len(posts)} posts for keyword: {normalized_keyword}")
            return posts
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching Reddit posts: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching Reddit posts: {str(e)}", exc_info=True)
            raise
