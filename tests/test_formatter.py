"""Tests for the formatter module."""

import json
import pytest

from trendsleuth.formatter import format_markdown, format_json, get_timestamp
from trendsleuth.analyzer import TrendAnalysis


class TestFormatter:
    """Tests for output formatters."""

    @pytest.fixture
    def analysis(self):
        """Create a sample analysis result."""
        return TrendAnalysis(
            topics=["AI Agents", "Machine Learning", "Natural Language Processing"],
            pain_points=["High costs", "Complex setup", "Lack of documentation"],
            questions=["How to start?", "What tools to use?", "Best practices?"],
            summary="The community shows strong interest in AI agents with some concerns about accessibility.",
            sentiment="positive",
        )

    def test_get_timestamp(self):
        """Test timestamp generation."""
        timestamp = get_timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0

    def test_format_markdown(self, analysis):
        """Test markdown output formatting."""
        result = format_markdown(
            subreddit="r/ai",
            analysis=analysis,
            token_usage={"input_tokens": 100, "output_tokens": 50},
            cost=0.0025,
        )

        assert "# Trend Analysis: r/ai" in result
        assert "## Summary" in result
        assert "## Trending Topics" in result
        assert "## Pain Points" in result
        assert "## Questions" in result
        assert "## Metrics" in result
        assert "AI Agents" in result
        assert "High costs" in result

    def test_format_json(self, analysis):
        """Test JSON output formatting."""
        result = format_json(
            subreddit="r/ai",
            analysis=analysis,
            token_usage={"input_tokens": 100, "output_tokens": 50},
            cost=0.0025,
        )

        data = json.loads(result)
        assert data["subreddit"] == "r/ai"
        assert data["analysis"]["topics"] == analysis.topics
        assert data["analysis"]["pain_points"] == analysis.pain_points
        assert data["analysis"]["questions"] == analysis.questions
        assert "timestamp" in data
        assert "token_usage" in data
        assert "estimated_cost" in data

    def test_format_markdown_minimal(self, analysis):
        """Test markdown output without token usage."""
        result = format_markdown(
            subreddit="r/test",
            analysis=analysis,
        )

        assert "# Trend Analysis: r/test" in result
        # Should not have Metrics section when no token info provided
        assert "## Metrics" not in result

    def test_format_json_minimal(self, analysis):
        """Test JSON output without token usage."""
        result = format_json(
            subreddit="r/test",
            analysis=analysis,
        )

        data = json.loads(result)
        assert "token_usage" not in data
        assert "estimated_cost" not in data
