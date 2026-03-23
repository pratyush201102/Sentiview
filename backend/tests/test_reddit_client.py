import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from backend.app.services.reddit_client import RedditClient


@pytest.fixture
def reddit_client():
    """Create a RedditClient instance for testing."""
    return RedditClient()


@pytest.fixture
def mock_reddit_response():
    """Mock a typical Reddit API response."""
    return {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "abc123",
                        "author": "TestUser1",
                        "subreddit": "test_subreddit",
                        "title": "Test Post Title",
                        "selftext": "This is the post body content.",
                        "permalink": "/r/test_subreddit/comments/abc123/test_post/",
                        "created_utc": 1708000000,
                    }
                },
                {
                    "data": {
                        "id": "def456",
                        "author": "TestUser2",
                        "subreddit": "another_subreddit",
                        "title": "Another Post",
                        "selftext": "",
                        "permalink": "/r/another_subreddit/comments/def456/another_post/",
                        "created_utc": 1708000100,
                    }
                },
            ]
        }
    }


class TestRedditClientInitialization:
    """Test RedditClient instantiation and configuration."""

    def test_client_initializes_with_settings(self, reddit_client):
        """Client should initialize with base_url and user_agent from settings."""
        assert reddit_client.base_url is not None
        assert reddit_client.user_agent is not None
        assert isinstance(reddit_client.base_url, str)
        assert isinstance(reddit_client.user_agent, str)

    def test_client_strips_trailing_slash_from_base_url(self):
        """RedditClient should remove trailing slash from base_url."""
        with patch("backend.app.services.reddit_client.settings") as mock_settings:
            mock_settings.reddit_base_url = "https://www.reddit.com/"
            mock_settings.reddit_user_agent = "TestAgent"
            client = RedditClient()
            assert client.base_url == "https://www.reddit.com"


class TestSearchPostsValidation:
    """Test input validation for search_posts method."""

    def test_search_posts_rejects_empty_keyword(self, reddit_client):
        """search_posts should raise ValueError for empty keyword."""
        with pytest.raises(ValueError, match="Keyword cannot be empty"):
            reddit_client.search_posts("", limit=10)

    def test_search_posts_rejects_whitespace_only_keyword(self, reddit_client):
        """search_posts should raise ValueError for whitespace-only keyword."""
        with pytest.raises(ValueError, match="Keyword cannot be empty"):
            reddit_client.search_posts("   ", limit=10)

    def test_search_posts_rejects_non_integer_limit(self, reddit_client):
        """search_posts should raise ValueError for non-integer limit."""
        with pytest.raises(ValueError, match="Limit must be a positive integer"):
            reddit_client.search_posts("test", limit="10")  # type: ignore[arg-type]

    def test_search_posts_rejects_zero_limit(self, reddit_client):
        """search_posts should raise ValueError for zero limit."""
        with pytest.raises(ValueError, match="Limit must be a positive integer"):
            reddit_client.search_posts("test", limit=0)

    def test_search_posts_rejects_negative_limit(self, reddit_client):
        """search_posts should raise ValueError for negative limit."""
        with pytest.raises(ValueError, match="Limit must be a positive integer"):
            reddit_client.search_posts("test", limit=-5)

    def test_search_posts_normalizes_keyword_whitespace(self, reddit_client, mock_reddit_response):
        """search_posts should normalize keyword whitespace."""
        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = mock_reddit_response
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            reddit_client.search_posts("  python  machine  learning  ", limit=5)
            
            # Check that the normalized keyword was used in the API call
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["q"] == "python  machine  learning"


class TestSearchPostsSuccess:
    """Test successful post fetching and data transformation."""

    def test_search_posts_returns_list_of_dicts(self, reddit_client, mock_reddit_response):
        """search_posts should return a list of post dictionaries."""
        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = mock_reddit_response
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            posts = reddit_client.search_posts("python", limit=10)

            assert isinstance(posts, list)
            assert len(posts) == 2

    def test_search_posts_transforms_data_correctly(self, reddit_client, mock_reddit_response):
        """search_posts should transform Reddit API response into expected format."""
        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = mock_reddit_response
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            posts = reddit_client.search_posts("test", limit=10)

            first_post = posts[0]
            assert first_post["source_post_id"] == "abc123"
            assert first_post["author"] == "TestUser1"
            assert first_post["subreddit"] == "test_subreddit"
            assert first_post["title"] == "Test Post Title"
            assert first_post["body"] == "This is the post body content."
            assert first_post["permalink"] == "https://www.reddit.com/r/test_subreddit/comments/abc123/test_post/"
            assert isinstance(first_post["posted_at"], datetime)

    def test_search_posts_converts_unix_timestamp_to_datetime(self, reddit_client, mock_reddit_response):
        """search_posts should properly convert Unix timestamps to datetime objects."""
        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = mock_reddit_response
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            posts = reddit_client.search_posts("test", limit=10)

            first_post = posts[0]
            expected_datetime = datetime.fromtimestamp(1708000000, tz=timezone.utc)
            assert first_post["posted_at"] == expected_datetime

    def test_search_posts_handles_missing_optional_fields(self, reddit_client):
        """search_posts should handle posts with missing optional fields."""
        incomplete_response = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "xyz789",
                            "author": None,  # Missing author
                            "subreddit": "test",
                            "title": "Test",
                            # Missing selftext
                            "permalink": "/r/test/comments/xyz789/test/",
                            # Missing created_utc
                        }
                    }
                ]
            }
        }

        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = incomplete_response
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            posts = reddit_client.search_posts("test", limit=10)
            
            assert len(posts) == 1
            assert posts[0]["author"] is None
            assert posts[0]["body"] == ""
            assert posts[0]["posted_at"] is None

    def test_search_posts_returns_empty_list_for_no_results(self, reddit_client):
        """search_posts should return empty list when no posts found."""
        empty_response = {"data": {"children": []}}

        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = empty_response
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            posts = reddit_client.search_posts("nonexistent_topic_xyz", limit=10)

            assert posts == []

    def test_search_posts_sends_correct_api_parameters(self, reddit_client, mock_reddit_response):
        """search_posts should send correct parameters to Reddit API."""
        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = mock_reddit_response
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            reddit_client.search_posts("python programming", limit=25)

            # Verify the API call was made with correct parameters
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            
            assert call_args[0][0] == f"{reddit_client.base_url}/search.json"
            assert call_args[1]["params"]["q"] == "python programming"
            assert call_args[1]["params"]["limit"] == 25
            assert call_args[1]["params"]["sort"] == "new"
            assert call_args[1]["headers"]["User-Agent"] == reddit_client.user_agent


class TestSearchPostsErrorHandling:
    """Test error handling in search_posts method."""

    def test_search_posts_raises_on_http_error(self, reddit_client):
        """search_posts should raise httpx.HTTPError on HTTP failures."""
        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("HTTP 429: Too Many Requests")
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(Exception):
                reddit_client.search_posts("test", limit=10)

    def test_search_posts_handles_malformed_json(self, reddit_client):
        """search_posts should handle malformed JSON responses gracefully."""
        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError):
                reddit_client.search_posts("test", limit=10)

    def test_search_posts_handles_timeout(self, reddit_client):
        """search_posts should handle HTTP timeouts."""
        import httpx
        
        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.TimeoutException):
                reddit_client.search_posts("test", limit=10)

    def test_search_posts_handles_connection_error(self, reddit_client):
        """search_posts should handle connection errors."""
        import httpx
        
        with patch("backend.app.services.reddit_client.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.side_effect = httpx.ConnectError("Failed to connect to Reddit")
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.ConnectError):
                reddit_client.search_posts("test", limit=10)
