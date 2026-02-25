from datetime import datetime, timezone

import httpx

from backend.app.config import settings


class RedditClient:
    def __init__(self) -> None:
        self.base_url = settings.reddit_base_url.rstrip("/")
        self.user_agent = settings.reddit_user_agent

    def search_posts(self, keyword: str, limit: int) -> list[dict]:
        url = f"{self.base_url}/search.json"
        params = {
            "q": keyword,
            "sort": "new",
            "limit": limit,
            "restrict_sr": "false",
            "type": "link",
        }
        headers = {"User-Agent": self.user_agent}

        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()

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

        return posts
