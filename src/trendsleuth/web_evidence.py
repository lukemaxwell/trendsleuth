"""Web evidence gathering using Brave Search."""

import logging
from dataclasses import dataclass

from rich.progress import Progress

from trendsleuth.brave import BraveClient, BraveConfig
from trendsleuth.web_scraper import fetch_page_text
from trendsleuth.analyzer import Analyzer, Evidence

logger = logging.getLogger(__name__)


@dataclass
class WebSearchConfig:
    """Configuration for web search."""

    limit: int = 15
    max_queries: int = 30
    results_per_query: int = 5


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


def fetch_search_result_urls(
    queries: list[str],
    brave_config: BraveConfig,
    search_config: WebSearchConfig,
    progress: Progress,
    ignore_urls: set[str] | None = None,
) -> set[str]:
    """Fetch search result urls for a list of queries.

    Args:
        queries: List of search queries
        brave_config: Brave API configuration
        search_config: Web search configuration (for results per query)
        progress: Progress instance for tracking progress
        ignore_urls: Set of URLs to ignore (e.g. Reddit URLs)

    Returns:
        Set of URLs
    """
    ignore_urls = ignore_urls or set()
    task_id = progress.add_task("[cyan]Performing web search...", total=len(queries))
    brave_client = BraveClient(brave_config)
    # Collect URLs
    urls = set()
    for query in queries:
        for result in brave_client.search(query, count=search_config.results_per_query):
            if result.url and result.url not in urls and result.url not in ignore_urls:
                urls.add(result.url)
        progress.advance(task_id)
    return urls


def gather_web_evidence(
    niche: str,
    pain_points: list[str],
    questions: list[str],
    topics: list[str],
    brave_config: BraveConfig,
    search_config: WebSearchConfig,
    analyzer: Analyzer,
    reddit_urls: set[str],
    progress: Progress,
) -> list[Evidence]:
    """Gather evidence from web search.

    Args:
        niche: The niche being analyzed
        pain_points: List of pain points from analysis
        questions: List of questions from analysis
        topics: List of trending topics from analysis
        brave_config: Brave API configuration
        search_config: Web search configuration
        analyzer: Analyzer instance for quote extraction
        reddit_urls: Set of Reddit URLs to dedupe against
        progress: Progress instance for tracking progress

    Returns:
        List of evidence items
    """
    # Generate web search queries
    queries = generate_search_queries(niche, pain_points, questions, topics)
    queries = queries[: search_config.max_queries]  # Cap total queries
    urls = set()
    # Fetch urls from search results
    urls = fetch_search_result_urls(
        queries=queries,
        brave_config=brave_config,
        search_config=search_config,
        ignore_urls=reddit_urls,
        progress=progress,
    )

    logger.info(f"Found {len(urls)} unique URLs (after deduplication)")
    # Fetch and extract quotes
    evidence_items = fetch_web_evidence_for_urls(
        urls=urls,
        analyzer=analyzer,
        niche=niche,
        search_config=search_config,
        progress=progress,
    )
    logger.info(f"Found {len(evidence_items)} evidence items")
    return evidence_items


def fetch_web_evidence_for_urls(
    urls: set[str],
    analyzer: Analyzer,
    niche: str,
    search_config: WebSearchConfig,
    progress: Progress,
) -> list[Evidence]:
    """Fetch web evidence for a set of URLs.

    Args:
        urls: Set of URLs to fetch evidence from
        analyzer: Analyzer instance for quote extraction
        niche: The niche being analyzed (for context in quote extraction)
        search_config: Web search configuration (for evidence limit)
        progress: Progress instance for tracking progress

    Returns:
        List of evidence items
    """
    total = min(len(urls), search_config.limit)
    task_id = progress.add_task(
        "[cyan]Fetching evidence from search results...", total=total
    )
    evidence_items: list[Evidence] = []
    for url in urls:
        if len(evidence_items) >= search_config.limit:
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

        progress.advance(task_id)

    # Limit to evidence_limit
    evidence_items = evidence_items[: search_config.limit]
    logger.info(f"Collected {len(evidence_items)} web evidence items")

    return evidence_items
