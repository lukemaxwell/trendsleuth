"""Tests for Brave Search API client."""

import pytest
import requests
from unittest.mock import Mock, patch

from trendsleuth.brave import BraveClient, BraveConfig


class TestBraveClient:
    """Tests for BraveClient."""

    @pytest.fixture
    def config(self):
        """Create a Brave config."""
        return BraveConfig(
            api_key="test_api_key",
            rate_limit_rps=2.0,
        )

    @pytest.fixture
    def client(self, config):
        """Create a Brave client instance."""
        return BraveClient(config)

    def test_init(self, client, config):
        """Test client initialization."""
        assert client.config == config
        assert client.last_request_time == 0
        assert client.min_interval == 0.5  # 1/2.0

    @patch("trendsleuth.brave.requests.Session")
    def test_search_success(self, mock_session_class, client):
        """Test successful search."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "url": "https://example.com/1",
                        "title": "Test Result 1",
                        "description": "Description 1",
                    },
                    {
                        "url": "https://example.com/2",
                        "title": "Test Result 2",
                        "description": "Description 2",
                    },
                ]
            }
        }
        mock_response.raise_for_status = Mock()

        # Mock session
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        client.session = mock_session

        # Execute search
        results = client.search("test query", count=5)

        # Verify
        assert len(results) == 2
        assert results[0].url == "https://example.com/1"
        assert results[0].title == "Test Result 1"
        assert results[1].url == "https://example.com/2"

    @patch("trendsleuth.brave.requests.Session")
    def test_search_no_results(self, mock_session_class, client):
        """Test search with no results."""
        mock_response = Mock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        client.session = mock_session

        results = client.search("no results query")

        assert results == []

    @patch("trendsleuth.brave.requests.Session")
    def test_search_api_error(self, mock_session_class, client):
        """Test search with API error."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.RequestException("API Error")
        client.session = mock_session

        results = client.search("error query")

        assert results == []

    @patch("trendsleuth.brave.requests.Session")
    def test_search_limits_results(self, mock_session_class, client):
        """Test that search respects count parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "url": f"https://example.com/{i}",
                        "title": f"Result {i}",
                        "description": f"Desc {i}",
                    }
                    for i in range(10)
                ]
            }
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        client.session = mock_session

        results = client.search("test", count=3)

        assert len(results) == 3

    @patch("trendsleuth.brave.time.sleep")
    def test_rate_limiting(self, mock_sleep, client):
        """Test that rate limiting is enforced."""

        # Mock time to simulate passage
        with patch("trendsleuth.brave.time.time") as mock_time:
            mock_time.side_effect = [0, 0.1, 0.1, 0.6]  # Simulate time progression

            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = {"web": {"results": []}}
            mock_response.raise_for_status = Mock()

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            client.session = mock_session

            # First request
            client.search("query1")

            # Second request (should trigger rate limit)
            client.search("query2")

            # Verify sleep was called
            assert mock_sleep.called
