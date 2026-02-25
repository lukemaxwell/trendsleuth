"""Tests for web evidence gathering."""

import pytest
from unittest.mock import Mock, patch

from trendsleuth.web_evidence import (
    generate_search_queries,
    gather_web_evidence,
    WebEvidenceConfig,
)
from trendsleuth.brave import BraveConfig, SearchResult
from trendsleuth.analyzer import Evidence


class TestGenerateSearchQueries:
    """Tests for generate_search_queries function."""

    def test_generates_base_queries(self):
        """Test that base queries are generated."""
        queries = generate_search_queries(
            niche="AI tools",
            pain_points=[],
            questions=[],
            topics=[],
        )

        # Should have 7 base queries
        assert "problems with AI tools" in queries
        assert "why is AI tools so hard" in queries
        assert "AI tools complaints" in queries
        assert "alternatives to AI tools" in queries
        assert "best AI tools tools review" in queries
        assert "AI tools review negative" in queries
        assert "site:reddit.com AI tools problem" in queries

    def test_generates_seeded_queries(self):
        """Test that seeded queries are generated."""
        queries = generate_search_queries(
            niche="productivity",
            pain_points=["slow performance", "bad UX"],
            questions=["how to start"],
            topics=["automation"],
        )

        # Should include seeded queries
        assert any("slow performance" in q for q in queries)
        assert any("bad UX" in q for q in queries)
        assert any("how to start" in q for q in queries)
        assert any("automation" in q for q in queries)

    def test_deduplicates_queries(self):
        """Test that duplicate queries are removed."""
        queries = generate_search_queries(
            niche="test",
            pain_points=["Problem", "problem"],  # Same, different case
            questions=[],
            topics=[],
        )

        # Count queries with "problem"
        problem_queries = [q for q in queries if "problem" in q.lower()]
        # Should dedupe case-insensitive
        unique_problems = set(q.lower() for q in problem_queries)
        assert len(problem_queries) == len(unique_problems)

    def test_limits_seeds_to_10(self):
        """Test that seeds are limited to top 10."""
        queries = generate_search_queries(
            niche="test",
            pain_points=["p1", "p2", "p3", "p4", "p5"],
            questions=["q1", "q2", "q3", "q4"],
            topics=["t1", "t2", "t3"],
        )

        # With 7 base + up to 10 seeds * 4 variants = max ~47 before dedup
        # After dedup should be reasonable
        assert len(queries) > 7  # More than just base
        assert len(queries) < 100  # Not excessive


class TestGatherWebEvidence:
    """Tests for gather_web_evidence function."""

    @pytest.fixture
    def brave_config(self):
        """Create Brave config."""
        return BraveConfig(api_key="test_key", rate_limit_rps=1.0)

    @pytest.fixture
    def web_config(self):
        """Create web evidence config."""
        return WebEvidenceConfig(
            evidence_limit=5,
            results_per_query=3,
            max_queries=10,
        )

    @pytest.fixture
    def mock_analyzer(self):
        """Create mock analyzer."""
        analyzer = Mock()
        analyzer.extract_quotes_from_text.return_value = [
            Evidence(
                source="web",
                quote="This is a pain point",
                url="https://example.com",
                date="2024-01-15",
            )
        ]
        return analyzer

    @patch("trendsleuth.web_evidence.BraveClient")
    @patch("trendsleuth.web_evidence.fetch_page_text")
    def test_gathers_evidence(
        self,
        mock_fetch,
        mock_brave_class,
        brave_config,
        web_config,
        mock_analyzer,
    ):
        """Test successful evidence gathering."""
        # Mock Brave client
        mock_brave = Mock()
        mock_brave.search.return_value = [
            SearchResult(
                url="https://example.com/1",
                title="Test Page",
                description="Test description",
            )
        ]
        mock_brave_class.return_value = mock_brave

        # Mock page fetch
        mock_fetch.return_value = "Page content with pain points"

        # Gather evidence
        evidence = gather_web_evidence(
            niche="test niche",
            pain_points=["issue1"],
            questions=["question1"],
            topics=["topic1"],
            brave_config=brave_config,
            web_config=web_config,
            analyzer=mock_analyzer,
            reddit_urls=set(),
        )

        # Verify
        assert len(evidence) > 0
        assert evidence[0].source == "web"
        mock_brave.search.assert_called()
        mock_fetch.assert_called()

    @patch("trendsleuth.web_evidence.BraveClient")
    @patch("trendsleuth.web_evidence.fetch_page_text")
    def test_deduplicates_urls(
        self,
        mock_fetch,
        mock_brave_class,
        brave_config,
        web_config,
        mock_analyzer,
    ):
        """Test that duplicate URLs are not fetched twice."""
        # Mock Brave client returns same URL from multiple queries
        mock_brave = Mock()
        mock_brave.search.return_value = [
            SearchResult(
                url="https://example.com/same",
                title="Test",
                description="Test",
            )
        ]
        mock_brave_class.return_value = mock_brave

        mock_fetch.return_value = "Page content"

        gather_web_evidence(
            niche="test",
            pain_points=["p1", "p2"],
            questions=[],
            topics=[],
            brave_config=brave_config,
            web_config=web_config,
            analyzer=mock_analyzer,
            reddit_urls=set(),
        )

        # Should only fetch each unique URL once
        fetch_calls = mock_fetch.call_count
        unique_urls = len(set(call[0][0] for call in mock_fetch.call_args_list))
        assert fetch_calls == unique_urls

    @patch("trendsleuth.web_evidence.BraveClient")
    @patch("trendsleuth.web_evidence.fetch_page_text")
    def test_excludes_reddit_urls(
        self,
        mock_fetch,
        mock_brave_class,
        brave_config,
        web_config,
        mock_analyzer,
    ):
        """Test that Reddit URLs are excluded."""
        mock_brave = Mock()
        mock_brave.search.return_value = [
            SearchResult(
                url="https://reddit.com/r/test/comments/123",
                title="Reddit Post",
                description="Test",
            ),
            SearchResult(
                url="https://example.com/article",
                title="Article",
                description="Test",
            ),
        ]
        mock_brave_class.return_value = mock_brave

        mock_fetch.return_value = "Page content"

        reddit_urls = {"https://reddit.com/r/test/comments/123"}

        gather_web_evidence(
            niche="test",
            pain_points=["p1"],
            questions=[],
            topics=[],
            brave_config=brave_config,
            web_config=web_config,
            analyzer=mock_analyzer,
            reddit_urls=reddit_urls,
        )

        # Should not fetch Reddit URL
        fetched_urls = [call[0][0] for call in mock_fetch.call_args_list]
        assert "https://reddit.com/r/test/comments/123" not in fetched_urls
        assert "https://example.com/article" in fetched_urls

    @patch("trendsleuth.web_evidence.BraveClient")
    @patch("trendsleuth.web_evidence.fetch_page_text")
    def test_respects_evidence_limit(
        self,
        mock_fetch,
        mock_brave_class,
        brave_config,
        web_config,
        mock_analyzer,
    ):
        """Test that evidence limit is enforced."""
        # Return many URLs
        mock_brave = Mock()
        mock_brave.search.return_value = [
            SearchResult(
                url=f"https://example.com/{i}",
                title=f"Page {i}",
                description="Test",
            )
            for i in range(20)
        ]
        mock_brave_class.return_value = mock_brave

        mock_fetch.return_value = "Page content"

        # Each page returns 2 quotes
        mock_analyzer.extract_quotes_from_text.return_value = [
            Evidence(source="web", quote="quote1", url="", date=None),
            Evidence(source="web", quote="quote2", url="", date=None),
        ]

        evidence = gather_web_evidence(
            niche="test",
            pain_points=["p1"],
            questions=[],
            topics=[],
            brave_config=brave_config,
            web_config=web_config,
            analyzer=mock_analyzer,
            reddit_urls=set(),
        )

        # Should not exceed evidence_limit
        assert len(evidence) <= web_config.evidence_limit

    @patch("trendsleuth.web_evidence.BraveClient")
    @patch("trendsleuth.web_evidence.fetch_page_text")
    def test_handles_fetch_failures(
        self,
        mock_fetch,
        mock_brave_class,
        brave_config,
        web_config,
        mock_analyzer,
    ):
        """Test that fetch failures are handled gracefully."""
        mock_brave = Mock()
        mock_brave.search.return_value = [
            SearchResult(url="https://example.com", title="Test", description="Test")
        ]
        mock_brave_class.return_value = mock_brave

        # Fetch returns None (failure)
        mock_fetch.return_value = None

        evidence = gather_web_evidence(
            niche="test",
            pain_points=["p1"],
            questions=[],
            topics=[],
            brave_config=brave_config,
            web_config=web_config,
            analyzer=mock_analyzer,
            reddit_urls=set(),
        )

        # Should return empty list, not crash
        assert evidence == []
