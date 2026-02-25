"""Web evidence gathering using Brave Search."""

import logging
from dataclasses import dataclass

from trendsleuth.brave import BraveClient, BraveConfig
from trendsleuth.web_scraper import fetch_page_text
from trendsleuth.analyzer import Analyzer, Evidence

logger = logging.getLogger(__name__)


@dataclass
class WebEvidenceConfig:
    """Configuration for web evidence gathering."""

    evidence_limit: int = 15
    results_per_query: int = 5
    max_queries: int = 30


def generate_search_queries(
    niche: str,
    pain_points: list[str],
    questions: list[str],
    topics: list[str],
) -> list[str]:
    """Generate search queries for evidence gathering.

    Args:
        niche: The niche being analyzed
        pain_points: List of pain points from analysis
        questions: List of questions from analysis
        topics: List of trending topics from analysis

    Returns:
        Deduplicated list of search queries
    """
    queries = []

    # Base queries
    base_queries = [
        f"problems with {niche}",
        f"why is {niche} so hard",
        f"{niche} complaints",
        f"alternatives to {niche}",
        f"best {niche} tools review",
        f"{niche} review negative",
        f"site:reddit.com {niche} problem",
    ]
    queries.extend(base_queries)

    # Seeded queries from analysis (top 10 seeds)
    seeds = []
    seeds.extend(pain_points[:4])
    seeds.extend(questions[:3])
    seeds.extend(topics[:3])
    seeds = seeds[:10]  # Cap at 10 seeds

    for seed in seeds:
        queries.extend(
            [
                f"{niche} {seed} problem",
                f"{niche} {seed} complaint",
                f"{niche} {seed} review",
                f"{niche} {seed} alternative",
            ]
        )

    # Deduplicate (case/whitespace insensitive)
    seen = set()
    dedupe_queries = []
    for query in queries:
        normalized = " ".join(query.lower().split())
        if normalized not in seen:
            seen.add(normalized)
            dedupe_queries.append(query)

    logger.info(f"Generated {len(dedupe_queries)} unique queries")
    return dedupe_queries


def gather_web_evidence(
    niche: str,
    pain_points: list[str],
    questions: list[str],
    topics: list[str],
    brave_config: BraveConfig,
    web_config: WebEvidenceConfig,
    analyzer: Analyzer,
    reddit_urls: set[str],
) -> list[Evidence]:
    """Gather evidence from web search.

    Args:
        niche: The niche being analyzed
        pain_points: List of pain points from analysis
        questions: List of questions from analysis
        topics: List of trending topics from analysis
        brave_config: Brave API configuration
        web_config: Web evidence configuration
        analyzer: Analyzer instance for quote extraction
        reddit_urls: Set of Reddit URLs to dedupe against

    Returns:
        List of evidence items
    """
    # Generate queries
    queries = generate_search_queries(niche, pain_points, questions, topics)
    queries = queries[: web_config.max_queries]  # Cap total queries

    # Initialize Brave client
    brave_client = BraveClient(brave_config)

    # Collect URLs
    all_urls = set()
    url_metadata = {}  # url -> {title, description}

    logger.info(f"Running {len(queries)} search queries...")
    for query in queries:
        results = brave_client.search(query, count=web_config.results_per_query)
        for result in results:
            if (
                result.url
                and result.url not in all_urls
                and result.url not in reddit_urls
            ):
                all_urls.add(result.url)
                url_metadata[result.url] = {
                    "title": result.title,
                    "description": result.description,
                }

    logger.info(f"Found {len(all_urls)} unique URLs (after deduplication)")

    # Fetch and extract quotes
    evidence_items: list[Evidence] = []
    for url in all_urls:
        if len(evidence_items) >= web_config.evidence_limit:
            break

        # Fetch page text
        page_text = fetch_page_text(url)
        if not page_text:
            continue

        # Extract quotes using LLM
        quotes = analyzer.extract_quotes_from_text(
            text=page_text,
            niche=niche,
            url=url,
            max_quotes=2,
        )

        if quotes:
            evidence_items.extend(quotes)
            logger.debug(f"Extracted {len(quotes)} quotes from {url}")

    # Limit to evidence_limit
    evidence_items = evidence_items[: web_config.evidence_limit]
    logger.info(f"Collected {len(evidence_items)} web evidence items")

    return evidence_items
