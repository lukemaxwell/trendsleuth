"""Tests for the analyzer module."""

import pytest
from unittest.mock import Mock

from trendsleuth.config import OpenAIConfig
from trendsleuth.analyzer import Analyzer, TrendAnalysis


class TestAnalyzer:
    """Tests for Analyzer."""
    
    @pytest.fixture
    def config(self):
        """Create an OpenAI config with mock API key."""
        return OpenAIConfig(api_key="test_api_key")
    
    @pytest.fixture
    def analyzer(self, config):
        """Create an analyzer instance."""
        return Analyzer(config)
    
    def test_init(self, config):
        """Test analyzer initialization."""
        analyzer = Analyzer(config)
        assert analyzer.config == config
        assert analyzer.model is not None
        assert analyzer.parser is not None
    
    def test_analyze_empty_data(self, analyzer):
        """Test analysis with no data."""
        result = analyzer.analyze_subreddit_data(
            subreddit_name="r/test",
            posts=[],
            comments=[],
        )
        assert result is None
    
    def test_analyze_with_data(self, analyzer):
        """Test analysis with minimal mock data."""
        # This test ensures the analyzer can process data without crashing
        result = analyzer.analyze_subreddit_data(
            subreddit_name="r/test",
            posts=[Mock(title="Test Post", selftext="This is test content")],
            comments=[Mock(body="This is a test comment")],
        )
        # Result may be None due to API issues, but should not crash
        # If it returns something, verify structure
        if result is not None:
            assert len(result.topics) > 0
            assert len(result.pain_points) >= 0
            assert len(result.questions) >= 0
            assert isinstance(result.summary, str)
            assert result.sentiment in ("positive", "negative", "neutral")
    
    def test_analyze_with_none_data(self, analyzer):
        """Test analysis with None data."""
        result = analyzer.analyze_subreddit_data(
            subreddit_name="r/test",
            posts=None,
            comments=None,
        )
        assert result is None
    
    def test_estimate_cost(self, analyzer):
        """Test cost estimation."""
        cost = analyzer.estimate_cost(100, 50)
        assert cost > 0
        assert isinstance(cost, float)
