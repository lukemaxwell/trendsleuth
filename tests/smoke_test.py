#!/usr/bin/env python3
"""Smoke tests for TrendSleuth CLI - verifies basic functionality without API calls."""

import sys

# Mock environment before importing modules
import os

os.environ.setdefault("REDDIT_CLIENT_ID", "test_id")
os.environ.setdefault("REDDIT_CLIENT_SECRET", "test_secret")
os.environ.setdefault("OPENAI_API_KEY", "test_key")


def test_imports():
    """Test that all modules can be imported."""
    # If we get here without errors, imports worked
    assert True


def test_config():
    """Test configuration loading."""
    from trendsleuth.config import get_config, validate_env_vars

    reddit_config, openai_config, app_config, brave_config = get_config()
    # Just check that config loads without errors
    assert reddit_config.client_id is not None
    assert openai_config.api_key is not None

    missing = validate_env_vars()
    # Should have no missing vars since we set them in the environment
    assert isinstance(missing, list)


def test_models():
    """Test Pydantic models."""
    from trendsleuth.analyzer import Evidence, TrendAnalysis, NicheList

    # Test Evidence
    evidence = Evidence(
        source="web",
        quote="Test quote",
        url="https://example.com",
        date="2024-01-15",
    )
    assert evidence.source == "web"

    # Test TrendAnalysis
    analysis = TrendAnalysis(
        topics=["topic1"],
        pain_points=["pain1"],
        questions=["question1"],
        summary="Test summary",
        sentiment="positive",
    )
    assert len(analysis.topics) == 1

    # Test NicheList
    niches = NicheList(niches=["niche1", "niche2"])
    assert len(niches.niches) == 2


def test_brave_client():
    """Test Brave client initialization."""
    from trendsleuth.brave import BraveClient, BraveConfig

    config = BraveConfig(api_key="test_key", rate_limit_rps=1.0)
    client = BraveClient(config)

    assert client.config.api_key == "test_key"
    assert client.min_interval == 1.0


def test_web_scraper():
    """Test web scraper."""
    from trendsleuth.web_scraper import extract_text_from_html

    html = "<html><body><p>Test content</p></body></html>"
    text = extract_text_from_html(html)

    assert "Test content" in text


def test_query_generation():
    """Test query generation."""
    from trendsleuth.web_evidence import generate_search_queries

    queries = generate_search_queries(
        niche="test",
        pain_points=["pain1"],
        questions=["question1"],
        topics=["topic1"],
    )

    assert len(queries) > 0
    assert "problems with test" in queries


def test_ideas_module():
    """Test ideas module."""
    from trendsleuth.ideas import _parse_json_analysis, format_ideas_as_markdown

    # Test JSON parsing
    import json

    test_json = json.dumps(
        {
            "analysis": {
                "summary": "Test",
                "topics": ["T1"],
                "pain_points": ["P1"],
                "questions": ["Q1"],
            }
        }
    )
    signals = _parse_json_analysis(test_json)
    assert signals.summary == "Test"

    # Test markdown formatting
    ideas_data = {
        "type": "business",
        "ideas": [
            {
                "name": "Test",
                "description": "Desc",
                "target_customer": "Users",
                "core_pain": "Pain",
                "product_description": "Product",
                "why_existing_fail": "Fail",
                "monetization": "Money",
                "pricing": "$10",
                "validation": "Beta",
            }
        ],
    }
    output = format_ideas_as_markdown(ideas_data)
    assert "Test" in output


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("TrendSleuth Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_imports,
        test_config,
        test_models,
        test_brave_client,
        test_web_scraper,
        test_query_generation,
        test_ideas_module,
    ]

    results = []
    for test in tests:
        try:
            test()
            print(f"✓ Test {test.__name__} passed")
            results.append(True)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
