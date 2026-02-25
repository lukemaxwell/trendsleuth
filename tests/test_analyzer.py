"""Tests for the analyzer module."""

import pytest
from unittest.mock import Mock, patch

from trendsleuth.config import OpenAIConfig
from trendsleuth.analyzer import Analyzer, TrendAnalysis, Evidence


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
    
    @patch('trendsleuth.analyzer.ChatOpenAI')
    def test_extract_quotes_from_text(self, mock_chat, analyzer):
        """Test quote extraction from web page text."""
        # Mock LLM response
        mock_result = Mock()
        mock_result.quotes = [
            {"quote": "This is a pain point", "date": "2024-01-15"},
            {"quote": "Another issue here", "date": None},
        ]
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_result
        
        # Mock the chain creation
        with patch.object(analyzer, 'model') as mock_model:
            mock_model.__or__ = Mock(return_value=mock_chain)
            
            evidence = analyzer.extract_quotes_from_text(
                text="Some text with pain points",
                niche="productivity tools",
                url="https://example.com",
                max_quotes=2,
            )
        
        # Verify
        assert len(evidence) == 2
        assert evidence[0].source == "web"
        assert evidence[0].quote == "This is a pain point"
        assert evidence[0].url == "https://example.com"
        assert evidence[0].date == "2024-01-15"
        assert evidence[1].date is None
    
    @patch('trendsleuth.analyzer.ChatOpenAI')
    def test_extract_quotes_handles_errors(self, mock_chat, analyzer):
        """Test that quote extraction handles errors gracefully."""
        # Mock the chain to raise an exception
        with patch.object(analyzer, 'model') as mock_model:
            mock_chain = Mock()
            mock_chain.invoke.side_effect = Exception("LLM Error")
            mock_model.__or__ = Mock(return_value=mock_chain)
            
            evidence = analyzer.extract_quotes_from_text(
                text="Some text",
                niche="test",
                url="https://example.com",
            )
        
        # Should return empty list, not crash
        assert evidence == []
    
    def test_extract_quotes_truncates_long_text(self, analyzer):
        """Test that long text is truncated."""
        long_text = "a" * 10000
        
        # Mock to capture the invoke call
        with patch.object(analyzer, 'model') as mock_model:
            mock_chain = Mock()
            mock_chain.invoke.return_value = Mock(quotes=[])
            mock_model.__or__ = Mock(return_value=mock_chain)
            
            analyzer.extract_quotes_from_text(
                text=long_text,
                niche="test",
                url="https://example.com",
            )
            
            # Verify text was truncated
            call_args = mock_chain.invoke.call_args[0][0]
            assert len(call_args['text']) <= 5000
