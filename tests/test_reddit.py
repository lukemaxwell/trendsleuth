"""Tests for the Reddit client."""

import pytest
from unittest.mock import Mock, patch

from trendsleuth.config import RedditConfig
from trendsleuth.reddit import RedditClient


class TestRedditClient:
    """Tests for RedditClient."""

    @pytest.fixture
    def config(self):
        """Create a Reddit config with mock credentials."""
        return RedditConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            user_agent="TestAgent/1.0",
        )

    @pytest.fixture
    def client(self, config):
        """Create a Reddit client instance."""
        return RedditClient(config)

    def test_init(self, config):
        """Test client initialization."""
        client = RedditClient(config)
        assert client.config == config
        assert client._client is None

    def test_get_subreddit_posts_empty(self, client):
        """Test fetching posts from a non-existent subreddit."""
        result = client.get_subreddit_posts("r/doesnotexist12345", limit=5)
        assert result == []

    def test_search_subreddits_empty(self, client):
        """Test searching for subreddits with no results."""
        result = client.search_subreddits("thisisnotarealsubredditxyz123", limit=5)
        # Should return empty list, not fail
        assert isinstance(result, list)

    @patch("trendsleuth.reddit.praw.Reddit")
    def test_client_creation(self, mock_praw, config):
        """Test that the Reddit client is created correctly."""
        mock_reddit_instance = Mock()
        mock_praw.return_value = mock_reddit_instance

        client = RedditClient(config)
        _ = client.client  # Access the property to trigger creation

        mock_praw.assert_called_once()
        call_kwargs = mock_praw.call_args.kwargs
        assert call_kwargs["client_id"] == "test_client_id"
        assert call_kwargs["client_secret"] == "test_client_secret"
        assert call_kwargs["user_agent"] == "TestAgent/1.0"
